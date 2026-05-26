# -*- coding: utf-8 -*-

import logging
from datetime import timedelta, datetime as dt
import pytz
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class ContractRenewalSettings(models.Model):
    """
    Settings for contract renewal behavior (parámetros globales).

    Singleton pattern: Only one record per company.
    Almacena parámetros globales para la renovación automática.
    IMPORTANTE: La habilitación/deshabilitación se hace POR CONTRATO,
    no de forma global.
    """
    _name = 'customer.contract.renewal.settings'
    _description = 'Configuración de renovación de contratos'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )

    renewal_period_days = fields.Integer(
        string='Período de renovación (días)',
        default=365,
        help='Número de días que se extiende el contrato en cada renovación (típicamente 365 días = 1 año).',
    )

    renewal_notification_days = fields.Integer(
        string='Notificar con X días de anticipación',
        default=30,
        help='Días antes de la fecha de vencimiento para enviar notificaciones de próxima renovación.',
    )

    allow_manual_renewal = fields.Boolean(
        string='Permitir renovación manual',
        default=True,
        help='Si se activa, los usuarios pueden renovar contratos manualmente desde el formulario.',
    )

    last_renewal_run = fields.Datetime(
        string='Última ejecución de cron de renovación',
        readonly=True,
        help='Timestamp de la última ejecución del cron de renovación automática.',
    )

    renewal_batch_size = fields.Integer(
        string='Tamaño de lote para renovación',
        default=100,
        help='Número máximo de contratos a renovar por cada ciclo del cron (evita overload).',
    )

    _sql_constraints = [
        ('company_uniq', 'UNIQUE(company_id)', 'Solo puede existir una configuración por empresa.'),
    ]

    @api.model
    def get_settings(self):
        """
        Obtiene la configuración singleton para la empresa actual.
        Crea una si no existe.
        """
        settings = self.search([('company_id', '=', self.env.company.id)], limit=1)
        if not settings:
            settings = self.create({
                'company_id': self.env.company.id,
            })
        return settings


class CustomerContractRenewal(models.Model):
    """
    Mixin que añade lógica de renovación a CustomerContract.
    Maneja tanto renovación automática como manual con protección contra duplicados.
    """
    _name = 'customer.contract'
    _inherit = ['customer.contract']

    # =========================================================
    # CAMPOS DE RENOVACIÓN
    # =========================================================
    auto_renewal_enabled = fields.Boolean(
        string='Auto-renovación habilitada',
        default=True,
        tracking=True,
        help='Si está activo, este contrato se renovará automáticamente antes de su vencimiento.',
    )

    last_renewal_date = fields.Date(
        string='Última fecha de renovación',
        readonly=True,
        copy=False,
        help='Última vez que este contrato fue renovado (automática o manualmente).',
    )

    next_renewal_date = fields.Date(
        string='Próxima fecha de renovación',
        compute='_compute_next_renewal_date',
        store=True,
        help='Fecha estimada de la próxima renovación (automática o manual).',
    )

    renewal_locked = fields.Boolean(
        string='Renovación bloqueada (en progreso)',
        default=False,
        readonly=True,
        copy=False,
        help='Flag interno para evitar renovaciones concurrentes del mismo contrato.',
    )

    renewal_attempt_count = fields.Integer(
        string='Intentos de renovación fallidos',
        default=0,
        readonly=True,
        copy=False,
        help='Contador de intentos fallidos consecutivos de renovación automática.',
    )

    last_renewal_error = fields.Char(
        string='Último error de renovación',
        readonly=True,
        copy=False,
        help='Mensaje del último error durante renovación automática.',
    )

    renewal_history_ids = fields.One2many(
        'customer.contract.renewal.history',
        'contract_id',
        string='Historial de renovaciones',
        readonly=True,
        copy=False,
    )

    # =========================================================
    # COMPUTED FIELDS
    # =========================================================
    @api.depends('end_date', 'last_renewal_date', 'state')
    def _compute_next_renewal_date(self):
        """
        Calcula la próxima fecha de renovación.
        Para contratos activos: se renueva en end_date.
        Para contratos finalizados: null.
        """
        for record in self:
            if record.state == 'active' and record.end_date:
                record.next_renewal_date = record.end_date
            else:
                record.next_renewal_date = False

    # =========================================================
    # MÉTODOS DE RENOVACIÓN (CON LOCKS)
    # =========================================================
    def action_renew_contract_manual(self):
        """
        Acción manual de renovación: disponible en el formulario.
        Puede ser disparada por el usuario manualmente.
        """
        # Open a confirmation wizard that allows the user to set the new end_date
        # instead of letting them edit `end_date` directly. This ensures the
        # renewal flow is followed (validation, history, chatter message).
        self.ensure_one()

        settings = self.env['customer.contract.renewal.settings'].get_settings()
        if not settings.allow_manual_renewal:
            raise UserError('La renovación manual de contratos está deshabilitada.')

        if self.state != 'active':
            raise ValidationError(
                f'Solo se pueden renovar contratos activos. '
                f'Estado actual: {self.state}')

        if self.renewal_locked:
            raise UserError(
                'Este contrato está siendo renovado en este momento. Por favor, intenta más tarde.')

        # Default proposed new end date (use settings to suggest extension)
        try:
            default_new = (self.end_date + timedelta(days=settings.renewal_period_days)) if self.end_date else (fields.Date.context_today(self) + timedelta(days=settings.renewal_period_days))
        except Exception:
            default_new = self.end_date or fields.Date.context_today(self)

        renewal_view = self.env.ref(
            'customer_contract.view_customer_contract_renewal_wizard_form',
            raise_if_not_found=False,
        )

        return {
            'name': 'Renovar contrato',
            'type': 'ir.actions.act_window',
            'res_model': 'customer.contract.renewal.wizard',
            'view_mode': 'form',
            'view_id': renewal_view.id if renewal_view else False,
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_new_end_date': default_new,
            },
        }

    @api.model
    def _cron_renew_expiring_contracts(self):
        """
        CRON JOB: Se ejecuta cada minuto (configurable).
        Busca contratos que necesitan renovación automática y los renueva.
        
        Arquitectura de concurrencia:
        1. Busca contratos expirados/próximos a expirar con auto-renovación habilitada
        2. Utiliza locks a nivel de DB (SELECT FOR UPDATE) para evitar duplicados
        3. Procesa en lotes para no sobrecargar el servidor
        4. Registra intentos y errores en historial
        """
        _logger.info('=== INICIANDO CRON DE RENOVACIÓN DE CONTRATOS ===')
        
        settings = self.env['customer.contract.renewal.settings'].get_settings()
        # Use Bolivia timezone to compute 'today' (America/La_Paz)
        tz = pytz.timezone('America/La_Paz')
        utc_now = dt.utcnow().replace(tzinfo=pytz.UTC)
        local_now = utc_now.astimezone(tz)
        today = local_now.date()
        batch_size = settings.renewal_batch_size

        _logger.info(
            'Iniciando cron de renovación automática. Lote: %d contratos. Hoy: %s',
            batch_size,
            today,
        )

        # 1. Busca contratos que vencen hoy o hace poco CON AUTO-RENOVACIÓN HABILITADA
        # Condición: end_date <= hoy Y auto_renewal_enabled=True Y (nunca renovado O última renovación fue hace más de 1 día)
        domain = [
            ('state', '=', 'active'),
            ('auto_renewal_enabled', '=', True),  # CADA CONTRATO DECIDE SI SE RENUEVA
            ('end_date', '<=', today),
            ('renewal_locked', '=', False),
            '|',
            ('last_renewal_date', '=', False),  # Nunca ha sido renovado
            ('last_renewal_date', '<', today - timedelta(days=1)),  # O fue renovado hace > 1 día
        ]

        # 2. Ordena por fecha de vencimiento para procesar los más vencidos primero
        contracts_to_renew = self.search(
            domain,
            order='end_date ASC',
            limit=batch_size,
        )

        _logger.info('Encontrados %d contratos para renovar.', len(contracts_to_renew))

        if not contracts_to_renew:
            _logger.info('No hay contratos para renovar.')
            settings.last_renewal_run = fields.Datetime.now()
            return

        renewed_count = 0
        failed_count = 0

        for contract in contracts_to_renew:
            try:
                # 3. Usa transacción y lock para evitar concurrencia
                self.env.cr.execute(
                    'SELECT 1 FROM customer_contract WHERE id = %s FOR UPDATE NOWAIT',
                    (contract.id,),
                )

                # Recarga el registro para obtener el estado más reciente
                contract = contract.browse(contract.id)

                # Verifica que aún sea elegible después del lock
                if contract.renewal_locked:
                    _logger.debug(
                        'Contrato %s está bloqueado. Saltando.',
                        contract.name,
                    )
                    continue

                if contract.last_renewal_date and contract.last_renewal_date >= today:
                    _logger.debug(
                        'Contrato %s fue renovado hoy. Saltando.',
                        contract.name,
                    )
                    continue

                # 4. Ejecuta la renovación
                contract.with_context(renewal_triggered_by='cron')._renew_contract()
                renewed_count += 1

            except Exception as e:
                failed_count += 1
                _logger.exception(
                    'Error renovando contrato %s: %s',
                    contract.name,
                    str(e),
                )
                # Incrementa contador de fallos para seguimiento
                contract.renewal_attempt_count += 1
                contract.last_renewal_error = str(e)[:255]

        # 5. Actualiza settings con timestamp de ejecución
        settings.last_renewal_run = fields.Datetime.now()

        _logger.info(
            'Cron de renovación completado: %d renovados, %d fallidos.',
            renewed_count,
            failed_count,
        )

    def _renew_contract(self, proposed_new_end_date=None):
        """
        Lógica central de renovación de contrato.
        
        Proceso:
        1. Valida que el contrato sea renovable
        2. Marca como bloqueado (lock a nivel de modelo)
        3. Extiende la fecha de fin
        4. Registra en historial
        5. Envía notificaciones
        6. Desbloquea
        
        Protección contra duplicados:
        - Flag `renewal_locked` durante la operación
        - Validación de last_renewal_date reciente
        - Creación de record en historial para auditoría
        """
        self.ensure_one()

        if self.state != 'active':
            raise ValidationError(
                f'No se puede renovar un contrato no-activo. Estado: {self.state}'
            )

        settings = self.env['customer.contract.renewal.settings'].get_settings()
        # Use Bolivia timezone for contract renewal date
        tz = pytz.timezone('America/La_Paz')
        utc_now = dt.utcnow().replace(tzinfo=pytz.UTC)
        local_now = utc_now.astimezone(tz)
        today = local_now.date()
        renewal_period = settings.renewal_period_days
        
        # Guarda el old_end_date ANTES de modificar
        old_end_date = self.end_date

        # Bloquea para evitar renovaciones concurrentes
        self.write({'renewal_locked': True})

        try:
            # Determine the new end date: use the proposed one (from wizard)
            # if provided, otherwise use the configured renewal_period.
            if proposed_new_end_date:
                new_end_date = proposed_new_end_date
            else:
                new_end_date = old_end_date + timedelta(days=renewal_period)

            # Validate the provided new_end_date to avoid inconsistencies
            if new_end_date <= old_end_date:
                raise ValidationError('La nueva fecha de finalización debe ser posterior a la fecha anterior.')

            renewal_triggered_by = self.env.context.get('renewal_triggered_by', 'system')

            self.write({
                'end_date': new_end_date,
                'last_renewal_date': today,
                'renewal_attempt_count': 0,
                'last_renewal_error': False,
            })

            # Registra en historial para auditoría (usa old_end_date guardado)
            renewal_note = self.env.context.get('renewal_note')

            self.env['customer.contract.renewal.history'].create({
                'contract_id': self.id,
                'old_end_date': old_end_date,
                'new_end_date': new_end_date,
                'renewal_type': renewal_triggered_by,
                'notes': (
                    f'Contrato renovado por {renewal_triggered_by}. '
                    f'{renewal_note or ""}'.strip()
                ),
            })

            # Registra actividad en chatter con etiqueta amigable
            friendly_labels = {
                'cron': 'Automática',
                'manual': 'Manual',
                'system': 'Sistema',
            }
            trigger_label = friendly_labels.get(renewal_triggered_by, renewal_triggered_by)

            # Post a safe HTML message to chatter using Markup
            self.message_post(
                body=Markup(
                    f'<b>Contrato renovado</b><br/>'
                    f'Nueva vigencia hasta: <b>{new_end_date}</b><br/>'
                    f'Tipo de renovación: {trigger_label}'
                ),
                subject='Renovación de contrato',
            )

            _logger.info(
                'Contrato %s renovado exitosamente. Nueva fecha fin: %s',
                self.name,
                new_end_date,
            )

        except Exception:
            # Registra error pero no lanza (será capturado por cron)
            raise
        finally:
            # IMPORTANTE: Desbloquea siempre al finalizar
            self.write({'renewal_locked': False})

    # =========================================================
    # VALIDACIONES
    # =========================================================
    @api.constrains('renewal_locked', 'state')
    def _check_renewal_locked_state(self):
        """
        No debe haber contratos bloqueados de renovación durante > 1 hora.
        Si pasa, registra un warning.
        """
        # Este check se ejecutará en create/write si el campo cambia
        for record in self:
            if record.renewal_locked:
                _logger.warning(
                    'Contrato %s tiene renewal_locked=True. '
                    'Si permanece así más de 1 hora, contactar a administrador.',
                    record.name,
                )

    # =========================================================
    # HERRAMIENTAS ADMINISTRATIVAS
    # =========================================================
    def action_unlock_renewal(self):
        """
        Acción de administrador para desbloquear un contrato.
        Usar solo si el lock quedó "colgado" (error inesperado).
        """
        if not self.env.user.has_group('base.group_system'):
            raise UserError('Solo administradores pueden desbloquear renovaciones.')

        self.renewal_locked = False
        # Use Markup for chatter message
        self.message_post(
            body=Markup('Bloqueo de renovación desbloqueado por administrador.'),
        )
        _logger.warning(
            'Administrador %s desbloqueó renovación de contrato %s',
            self.env.user.name,
            self.name,
        )


class CustomerContractRenewalWizard(models.TransientModel):
    _name = 'customer.contract.renewal.wizard'
    _description = 'Wizard para renovación manual de contrato'

    contract_id = fields.Many2one('customer.contract', string='Contrato', required=True, readonly=True)
    old_end_date = fields.Date(related='contract_id.end_date', readonly=True)
    new_end_date = fields.Date(string='Nueva fecha de finalización', required=True)
    note = fields.Text(string='Notas')

    def action_confirm(self):
        self.ensure_one()
        if self.new_end_date <= self.old_end_date:
            raise ValidationError('La nueva fecha de finalización debe ser posterior a la fecha anterior.')
        contract = self.contract_id
        if contract.renewal_locked:
            raise UserError('Este contrato está siendo renovado en este momento.')
        try:
            contract.with_context(
                renewal_triggered_by='manual',
                renewal_note=self.note,
            )._renew_contract(proposed_new_end_date=self.new_end_date)
        except Exception as e:
            _logger.exception('Error in manual renewal wizard for contract %s', contract.name)
            raise UserError(f'Error al renovar contrato: {str(e)}')
        # Return action to reload the contract form so the updated end_date is visible
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'reload': True},
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class ContractRenewalHistory(models.Model):
    """
    Auditoría: Registra cada renovación realizada (automática o manual).
    Permite traceabilidad completa y debugging de problemas.
    """
    _name = 'customer.contract.renewal.history'
    _description = 'Historial de renovaciones de contrato'
    _order = 'create_date DESC'

    contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato',
        required=True,
        ondelete='cascade',
    )

    old_end_date = fields.Date(
        string='Fecha fin anterior',
        required=True,
    )

    new_end_date = fields.Date(
        string='Nueva fecha fin',
        required=True,
    )

    renewal_type = fields.Selection(
        [
            ('manual', 'Manual (usuario)'),
            ('cron', 'Automática (cron)'),
            ('system', 'Sistema (otra)'),
        ],
        string='Tipo de renovación',
        default='system',
        required=True,
    )

    created_by_user = fields.Many2one(
        'res.users',
        string='Usuario que realizó la renovación',
        default=lambda self: self.env.user,
        readonly=True,
    )

    notes = fields.Text(
        string='Notas',
        help='Detalles adicionales sobre la renovación.',
    )

    renewal_period_days = fields.Integer(
        string='Período de renovación (días)',
        compute='_compute_renewal_period_days',
    )

    @api.depends('old_end_date', 'new_end_date')
    def _compute_renewal_period_days(self):
        for record in self:
            if record.old_end_date and record.new_end_date:
                delta = record.new_end_date - record.old_end_date
                record.renewal_period_days = delta.days
            else:
                record.renewal_period_days = 0
