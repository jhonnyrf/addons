import os
import base64
import mimetypes
import logging
import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
_logger = logging.getLogger(__name__)


def _get_partner_mobile(partner):
    for field in ('mobile', 'x_mobile', 'celular'):
        val = getattr(partner, field, None)
        if val is not None:
            return val or ''
    return ''


# ---------------------------------------------------------------------------
# Constantes globales
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'application/pdf',
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}

REQUIRED_FROM_PENDING = ('mobile', 'address', 'plan_id', 'contract_date', 'installation_date')
REQUIRED_FROM_ACTIVE  = ('location_link', 'coordinates')


class CustomerContract(models.Model):
    _name        = 'customer.contract'
    _description = 'Contrato de Cliente ISP'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _rec_name    = 'name'

    _PARTNER_SYNC_FIELDS = (
        'partner_id',
        'contact_name',
        'phone',
        'mobile',
        'email',
        'address',
        'ci',
        'vat',
        'location_link',
        'coordinates',
    )

    # Nota:
    # El código de contrato puede repetirse entre versiones históricas cuando
    # se hace cambio de plan. Se controla por constrains Python que solo exista
    # una versión no reemplazada por código.

    # =========================================================
    # CLIENTE / CONTACTO
    # =========================================================
    name = fields.Char(
        string='Nº de Contrato',
        required=True,
        copy=False,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente / Empresa',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    contact_partner_id = fields.Many2one(
        'res.partner',
        string='Persona de contacto',
        domain="[('parent_id', '=', partner_id)]",
    )
    billing_responsible_type = fields.Selection(
        [
            ('client', 'Cliente del contrato'),
            ('other', 'Otra persona'),
        ],
        string='Responsable de facturación',
        default='client',
        tracking=True,
        help='Permite usar los datos del cliente del contrato o de otra persona.',
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string="Lead de origen",
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    customer_type = fields.Selection(
        [('person', 'Persona'), ('company', 'Empresa')],
        string='Tipo de cliente',
        compute='_compute_customer_type',
        store=True,
    )

    contact_name   = fields.Char(string='Nombre / Empresa')
    billing_name   = fields.Char(string='Nombre del facturante')
    billing_phone  = fields.Char(string='Teléfono del facturante')
    billing_ci     = fields.Char(string='CI del facturante')

    phone   = fields.Char(string='Teléfono')
    mobile  = fields.Char(string='Celular')
    email   = fields.Char(string='E-mail')
    address = fields.Char(string='Dirección')
    ci      = fields.Char(string='CI')
    vat     = fields.Char(string='NIT')

    # =========================================================
    # PLAN / SERVICIO
    # =========================================================
    plan_id = fields.Many2one(
        'internet.plan',
        string='Plan de Internet',
        domain=[('active', '=', True)],
        ondelete='restrict',
        tracking=True,
    )
    plan_speed = fields.Integer(
        string='Velocidad (Mbps)',
        related='plan_id.speed',
        readonly=True,
    )
    plan_identifier = fields.Char(
        string='Identificador del plan',
        related='plan_id.plan_identifier',
        readonly=True,
    )
    plan_price = fields.Float(
        string='Tarifa mensual (Bs)',
        related='plan_id.price',
        readonly=True,
    )
    plan_type = fields.Selection(
        related='plan_id.plan_type',
        string='Tipo de Plan',
        readonly=True,
    )

    payment_mode = fields.Selection(
        [
            ('prepaid', 'Prepago'),
            ('postpaid', 'Postpago'),
        ],
        string='Modalidad de pago',
        required=True,
        default='prepaid',
        tracking=True,
        help=(
            'Prepago: pagas antes de usar el servicio. '\
            'Postpago: pagas después de usar el servicio (facturación mensual).'
        ),
    )

    # =========================================================
    # VINCULACIÓN CON PARTNER.PLAN (contactos_ext) — referencia débil
    # Se guarda como Integer para no depender de contactos_ext en tiempo
    # de carga. La sincronización se hace en tiempo de ejecución.
    # =========================================================
    partner_plan_id = fields.Integer(
        string='ID Plan CF',
        copy=False,
        help='ID del registro partner.plan vinculado (módulo contactos_ext).',
    )

    # =========================================================
    # HISTORIAL DE CAMBIOS DE PLAN (contratos anteriores)
    # =========================================================
    previous_contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato anterior',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='Contrato que fue reemplazado por este al cambiar de plan.',
    )
    next_contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato siguiente',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='Nuevo contrato generado al cambiar el plan de este contrato.',
    )
    updated_contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato actualizado',
        related='next_contract_id',
        store=True,
        readonly=True,
        help='Referencia directa al contrato nuevo generado por cambio de plan.',
    )
    contract_history_ids = fields.One2many(
        'customer.contract',
        'previous_contract_id',
        string='Historial de contratos',
        readonly=True,
    )
    is_superseded = fields.Boolean(
        string='Reemplazado',
        default=False,
        readonly=True,
        copy=False,
        help='True cuando este contrato fue reemplazado por un cambio de plan.',
    )

    # =========================================================
    # FECHAS
    # =========================================================
    contract_date = fields.Date(
        string='Fecha de contrato',
        default=fields.Date.context_today,
        tracking=True,
    )
    installation_date = fields.Date(
        string='Fecha de Instalación',
        default=fields.Date.context_today,
        tracking=True,
    )
    end_date = fields.Date(
        string='Fecha de Finalización',
        tracking=True,
        default=lambda self: fields.Date.context_today(self) + timedelta(days=365),
    )
    termination_date = fields.Date(
        string='Fecha de Terminación',
        tracking=True,
        readonly=True,
        copy=False,
    )
    effective_end_date = fields.Date(
        string="Fecha fin efectiva",
        compute="_compute_effective_end_date",
        store=True,
    )

    # =========================================================
    # INFORMACIÓN ADICIONAL
    # =========================================================
    location_link = fields.Char(string='Link Ubicación')
    coordinates   = fields.Char(string='Coordenadas')

    # =========================================================
    # DOCUMENTO DEL CONTRATO
    # =========================================================
    contrato = fields.Binary(
        string='Archivo del Contrato',
        attachment=True,
    )
    contrato_filename = fields.Char(string='Nombre del archivo')
    contract_attachment_ids = fields.Many2many(
        'ir.attachment',
        'customer_contract_attachment_rel',
        'contract_id',
        'attachment_id',
        string='Archivos de contrato',
        copy=False,
        help='Permite adjuntar múltiples archivos del contrato (PDF/JPG/PNG).',
    )
    has_contract_documents = fields.Boolean(
        string='Tiene documentos de contrato',
        compute='_compute_has_contract_documents',
        store=False,
    )
    contrato_mimetype = fields.Char(
        string='Tipo MIME',
        compute='_compute_contrato_mimetype',
        store=True,
    )
    contrato_is_image = fields.Boolean(
        string='¿Es imagen?',
        compute='_compute_contrato_mimetype',
        store=True,
    )
    contrato_is_pdf = fields.Boolean(
        string='¿Es PDF?',
        compute='_compute_contrato_mimetype',
        store=True,
    )

    # =========================================================
    # ESTADO
    # =========================================================
    state = fields.Selection([
        ('draft',      'Borrador'),
        ('pending',    'Pendiente de Contrato'),
        ('signed',     'Contrato Registrado'),
        ('active',     'Activo'),
        ('terminated', 'Finalizado'),
    ], default='draft', tracking=True)

    # =========================================================
    # COMPUTED
    # =========================================================
    @api.depends('contrato_filename')
    def _compute_contrato_mimetype(self):
        for record in self:
            filename = (record.contrato_filename or '').lower()
            mime, _ = mimetypes.guess_type(filename)
            record.contrato_mimetype  = mime or False
            record.contrato_is_image  = mime in ('image/jpeg', 'image/png', 'image/jpg')
            record.contrato_is_pdf    = mime == 'application/pdf'

    @api.depends('contrato', 'contract_attachment_ids')
    def _compute_has_contract_documents(self):
        for record in self:
            record.has_contract_documents = bool(record.contrato or record.contract_attachment_ids)

    @api.depends('end_date', 'termination_date')
    def _compute_effective_end_date(self):
        for rec in self:
            rec.effective_end_date = rec.termination_date or rec.end_date

    @api.depends('effective_end_date')
    def _compute_expiration_alert(self):
        today = fields.Date.today()
        for rec in self:
            if rec.effective_end_date:
                delta = (rec.effective_end_date - today).days
                rec.is_expiring_soon = 0 <= delta <= 30

    @api.depends('partner_id.is_company')
    def _compute_customer_type(self):
        for record in self:
            record.customer_type = (
                'company' if record.partner_id and record.partner_id.is_company
                else 'person'
            )

    # =========================================================
    # ONCHANGE
    # =========================================================
    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.contact_name = self.partner_id.name  or ''
            self.phone        = self.partner_id.phone or ''
            self.mobile       = _get_partner_mobile(self.partner_id)
            self.email        = self.partner_id.email  or ''
            self.address      = self.partner_id.direccion or ''
            self.ci           = self.partner_id.ci     or ''
            self.vat          = self.partner_id.vat    or ''
            self.location_link = self.partner_id.ubicacion or ''
            self.coordinates   = self.partner_id.coordenadas or ''

            # Para empresas, facturación debe ser manual.
            if self.partner_id.is_company:
                self.billing_responsible_type = 'other'

        if self.billing_responsible_type == 'client' and self.partner_id and not self.partner_id.is_company:
            self._fill_billing_from_contract_snapshot()

    @api.onchange('contact_name', 'mobile', 'phone', 'ci')
    def _onchange_contract_billing_source_fields(self):
        if self.billing_responsible_type == 'client' and self.customer_type != 'company':
            self._fill_billing_from_contract_snapshot()

    @api.onchange('billing_responsible_type')
    def _onchange_billing_responsible_type(self):
        if self.billing_responsible_type == 'client':
            if self.customer_type == 'company':
                self.billing_responsible_type = 'other'
            else:
                self._fill_billing_from_contract_snapshot()
        else:
            self._clear_billing_fields()

    # =========================================================
    # OVERRIDE CREATE / WRITE
    # =========================================================
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'name' in fields_list and not res.get('name'):
            res['name'] = self._next_unique_contract_code()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self._next_unique_contract_code()
            self._prefill_partner_fields(vals)
            self._prefill_billing_fields(vals)
        records = super().create(vals_list)
        if not self.env.context.get('skip_contract_to_partner_sync'):
            records._sync_partner_from_contract()
        return records

    @api.model
    def _next_unique_contract_code(self):
        """Genera un código CF único incluso si la secuencia fue reiniciada."""
        for _attempt in range(50):
            seq_name = self.env['ir.sequence'].next_by_code('customer.contract') or 'CF-00001'
            candidate = self._normalize_contract_code(seq_name)
            if not self.search_count([('name', '=', candidate)]):
                return candidate

        # Fallback defensivo: calcular siguiente número desde contratos existentes.
        max_num = 0
        existing = self.search([('name', 'like', 'CF-%')])
        for rec in existing:
            match = re.search(r'(\d+)$', rec.name or '')
            if match:
                max_num = max(max_num, int(match.group(1)))
        return f"CF-{max_num + 1:05d}"

    @api.model
    def _normalize_contract_code(self, code):
        value = (code or '').strip()
        match = re.search(r'(\d+)$', value)
        if not match:
            return 'CF-00001'
        return f"CF-{int(match.group(1)):05d}"

    def write(self, vals):
        if 'partner_id' in vals:
            self._prefill_partner_fields(vals)
        billing_sync_needed = any(field in vals for field in ('billing_responsible_type', 'partner_id'))
        partner_sync_needed = any(field in vals for field in self._PARTNER_SYNC_FIELDS)
        result = super().write(vals)

        if billing_sync_needed and not self.env.context.get('skip_billing_sync'):
            for record in self:
                if record.billing_responsible_type == 'client' and record.partner_id:
                    record.with_context(skip_billing_sync=True).write({
                        'billing_name': record.contact_name or record.partner_id.name or '',
                        'billing_phone': record.mobile or record.phone or _get_partner_mobile(record.partner_id),
                        'billing_ci': record.ci or record.partner_id.ci or '',
                    })

        if partner_sync_needed and not self.env.context.get('skip_contract_to_partner_sync'):
            self._sync_partner_from_contract()

        return result

    def _sync_partner_from_contract(self):
        """Sincroniza snapshot del contrato hacia el contacto (res.partner)."""
        for record in self:
            partner = record.partner_id
            if not partner:
                continue

            vals = {}
            partner_fields = partner._fields

            if 'name' in partner_fields:
                vals['name'] = record.contact_name or partner.name or ''
            if 'phone' in partner_fields:
                vals['phone'] = record.phone or False
            if 'mobile' in partner_fields:
                vals['mobile'] = record.mobile or False
            if 'celular' in partner_fields:
                vals['celular'] = record.mobile or False
            if 'email' in partner_fields:
                vals['email'] = record.email or False
            if 'direccion' in partner_fields:
                vals['direccion'] = record.address or False
            if 'ci' in partner_fields:
                vals['ci'] = record.ci or False
            if 'vat' in partner_fields:
                vals['vat'] = record.vat or False
            if 'ubicacion' in partner_fields:
                vals['ubicacion'] = record.location_link or False
            if 'coordenadas' in partner_fields:
                vals['coordenadas'] = record.coordinates or False

            if vals:
                partner.with_context(skip_partner_to_lead_sync=True).sudo().write(vals)

    def _prefill_partner_fields(self, vals):
        partner_id = vals.get('partner_id')
        if not partner_id:
            return
        partner = self.env['res.partner'].browse(partner_id)
        vals.setdefault('contact_name', partner.name   or '')
        vals.setdefault('phone',        partner.phone  or '')
        vals.setdefault('mobile',       _get_partner_mobile(partner))
        vals.setdefault('email',        partner.email  or '')
        vals.setdefault('address',      partner.direccion or '')
        vals.setdefault('ci',           partner.ci     or '')
        vals.setdefault('vat',          partner.vat    or '')
        vals.setdefault('location_link', partner.ubicacion or '')
        vals.setdefault('coordinates',   partner.coordenadas or '')

    def _prefill_contact_fields(self, vals):
        contact_id = vals.get('contact_partner_id')
        if not contact_id or vals.get('billing_responsible_type', 'client') == 'client':
            return
        contact = self.env['res.partner'].browse(contact_id)
        vals.setdefault('billing_name',  contact.name  or '')
        vals.setdefault('billing_phone', contact.phone or '')
        vals.setdefault('billing_ci',    contact.ci    or '')

    def _prefill_billing_fields(self, vals):
        billing_type = vals.get('billing_responsible_type', 'client')

        if billing_type == 'client':
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                vals.setdefault('billing_name', vals.get('contact_name') or partner.name or '')
                vals.setdefault('billing_phone', vals.get('mobile') or vals.get('phone') or _get_partner_mobile(partner))
                vals.setdefault('billing_ci', vals.get('ci') or partner.ci or '')
            return

    def _fill_billing_from_partner(self):
        if self.partner_id:
            self.billing_name = self.partner_id.name or ''
            self.billing_phone = _get_partner_mobile(self.partner_id)
            self.billing_ci = self.partner_id.ci or ''
        else:
            self._clear_billing_fields()

    def _fill_billing_from_contract_snapshot(self):
        self.billing_name = self.contact_name or (self.partner_id.name if self.partner_id else '') or ''
        self.billing_phone = self.mobile or self.phone or (_get_partner_mobile(self.partner_id) if self.partner_id else '')
        self.billing_ci = self.ci or (self.partner_id.ci if self.partner_id else '') or ''

    def _clear_billing_fields(self):
        self.billing_name = ''
        self.billing_phone = ''
        self.billing_ci = ''

    def name_get(self):
        result = []
        for rec in self:
            code = rec.name or ''
            partner_name = rec.partner_id.name or ''
            display = f"{code} - {partner_name}" if code and partner_name else (code or partner_name or f"Contrato {rec.id}")
            result.append((rec.id, display))
        return result

    @api.depends('name', 'partner_id.name')
    def _compute_display_name(self):
        for rec in self:
            code = rec.name or ''
            partner_name = rec.partner_id.name or ''
            rec.display_name = f"{code} - {partner_name}" if code and partner_name else (code or partner_name or f"Contrato {rec.id}")

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        args = list(args or [])
        if name:
            args = ['|', ('name', operator, name), ('partner_id.name', operator, name)] + args
        return self._search(args, limit=limit, order=order)

    # =========================================================
    # CAMBIO DE PLAN — lógica principal COM-11
    # =========================================================
    def action_change_plan_wizard(self):
        """Abre wizard para cambiar el plan del contrato activo."""
        self.ensure_one()
        if self.state != 'active':
            raise ValidationError(
                "Solo se puede cambiar el plan de un contrato Activo."
            )
        return {
            'name': 'Cambiar plan del contrato',
            'type': 'ir.actions.act_window',
            'res_model': 'customer.contract.plan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id},
        }

    def action_apply_plan_change(self, new_plan_id, note='', contrato=False, contrato_filename='', contract_attachment_ids=None):
        """
        Ejecuta el cambio de plan:
        1. Marca el contrato actual como reemplazado (terminated + is_superseded)
        2. Crea un nuevo contrato con el nuevo plan
        3. Vincula ambos contratos (previous/next)
        4. Si tiene partner_plan_id, actualiza también el partner.plan
        """
        self.ensure_one()
        if self.state != 'active':
            raise ValidationError('Solo se puede cambiar el plan de un contrato activo.')

        today = fields.Date.context_today(self)
        new_plan = self.env['internet.plan'].browse(new_plan_id)
        if not new_plan.exists() or not new_plan.active:
            raise ValidationError('Debes seleccionar un plan activo y válido.')
        if self.plan_id and self.plan_id.id == new_plan.id:
            raise ValidationError('Selecciona un plan diferente al actual.')

        attachment_ids = contract_attachment_ids or []
        attachments = self.env['ir.attachment'].browse(attachment_ids)

        if contrato:
            self._validate_binary_contract_file(contrato, contrato_filename)
        if attachments:
            self._validate_attachment_recordset(attachments)

        # 1. Terminar el contrato actual marcándolo como reemplazado
        self.write({
            'state': 'terminated',
            'termination_date': today,
            'is_superseded': True,
        })
        self.message_post(
            body=f"Contrato reemplazado por cambio de plan a <b>{new_plan.name}</b>."
                 + (f" Motivo: {note}" if note else ""),
        )

        # 2. Crear nuevo contrato con el nuevo plan (conservando código)
        new_contract_vals = {
            'name': self.name,
            'plan_id': new_plan.id,
            'state': 'active',
            'contract_date': today,
            'installation_date': today,
            'end_date': today + timedelta(days=365),
            'termination_date': False,
            'is_superseded': False,
            'previous_contract_id': self.id,
            'next_contract_id': False,
            'partner_plan_id': self.partner_plan_id if self.partner_plan_id else 0,
        }
        if contrato:
            new_contract_vals.update({
                'contrato': contrato,
                'contrato_filename': contrato_filename or '',
            })
        if attachment_ids:
            new_contract_vals['contract_attachment_ids'] = [(6, 0, attachment_ids)]

        new_contract = self.with_context(change_plan_mode=True).copy({
            **new_contract_vals,
        })

        # 3. Vincular contrato actual → nuevo
        self.write({'next_contract_id': new_contract.id})

        # 3.b Actualizar referencias en CRM: si existe la oportunidad origen,
        # debe apuntar al nuevo contrato para que el CRM muestre el estado/plan
        # correcto (evita seguir mostrando el contrato finalizado).
        try:
            Lead = self.env['crm.lead']
            lead_records = self.lead_id
            if not lead_records:
                lead_records = Lead.search([('contract_id', '=', self.id)])

            if lead_records:
                # Reasignar la oportunidad al contrato nuevo desde la API del CRM.
                # Esto mantiene sincronizados los campos visibles de la tarjeta.
                lead_records.sync_contract_reference(new_contract)
                new_contract.write({'lead_id': lead_records[:1].id})
        except Exception:
            _logger.exception('Error actualizando leads al cambiar plan del contrato %s', self.id)

        # 4. Actualizar partner.plan si existe el vínculo (contactos_ext opcional)
        if self.partner_plan_id and 'partner.plan' in self.env:
            partner_plan = self.env['partner.plan'].browse(self.partner_plan_id)
            if partner_plan.exists():
                partner_plan.sync_from_contract(new_contract)
            new_contract.write({'partner_plan_id': self.partner_plan_id})

        new_contract.message_post(
            body=f"Contrato creado por cambio de plan desde <b>{self.name}</b>."
                 + (f" Plan anterior: {self.plan_id.name}." if self.plan_id else ""),
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuevo contrato',
            'res_model': 'customer.contract',
            'res_id': new_contract.id,
            'view_mode': 'form',
        }

    def action_open_updated_contract(self):
        self.ensure_one()
        if not self.updated_contract_id:
            raise UserError('Este contrato no tiene un contrato actualizado vinculado.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrato actualizado',
            'res_model': 'customer.contract',
            'res_id': self.updated_contract_id.id,
            'view_mode': 'form',
        }

    # =========================================================
    # VALIDACIONES POR ESTADO
    # =========================================================
    @api.constrains('state',
                    'mobile', 'address', 'plan_id', 'contract_date', 'installation_date',
                    'ci', 'vat', 'customer_type',
                    'contrato', 'contrato_filename', 'contrato_mimetype',
                    'location_link', 'coordinates',
                    'end_date')
    def _check_state_constraints(self):
        for record in self:
            state = record.state
            if state == 'draft':
                continue
            if state in ('pending', 'signed', 'active', 'terminated'):
                record._validate_pending_fields()
            if state in ('signed', 'active', 'terminated'):
                record._validate_signed_fields()
                record._validate_billing_fields()
            if state in ('active', 'terminated'):
                record._validate_active_fields()
            if state == 'terminated':
                record._validate_terminated_fields()

    @api.constrains('contract_date', 'installation_date')
    def _check_dates_consistency(self):
        for record in self:
            if record.contract_date and record.installation_date:
                if record.installation_date < record.contract_date:
                    raise ValidationError(
                        "La fecha de instalación no puede ser anterior "
                        "a la fecha de contrato."
                    )

    @api.constrains('name', 'is_superseded')
    def _check_unique_current_contract_code(self):
        for record in self:
            if not record.name or record.is_superseded:
                continue
            duplicate = self.search([
                ('id', '!=', record.id),
                ('name', '=', record.name),
                ('is_superseded', '=', False),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    "Ya existe un contrato vigente con el mismo número de contrato."
                )

    @api.constrains('name')
    def _check_contract_code_exists(self):
        if self.env.context.get('install_mode'):
            return
        if self.env.context.get('change_plan_mode'):
            return
        for record in self:
            if not record.name:
                continue
            existing = self.search([
                ('id', '!=', record.id),
                ('name', '=', record.name),
            ], limit=1)
            if existing:
                raise ValidationError(
                    f"El código de contrato '{record.name}' ya está en uso. "
                    "Por favor, use otro código o déjelo vacío para generar uno automáticamente."
                )

    @api.constrains('contrato', 'contrato_filename', 'contract_attachment_ids')
    def _check_contrato_file(self):
        for record in self:
            if record.contrato:
                record._validate_binary_contract_file(record.contrato, record.contrato_filename)
            record._validate_attachment_files()

    # =========================================================
    # MÉTODOS AUXILIARES DE VALIDACIÓN
    # =========================================================
    def _validate_pending_fields(self):
        field_labels = {
            'mobile':            'Celular',
            'address':           'Dirección',
            'plan_id':           'Plan de Internet',
            'plan_identifier':   'Identificador del plan',
            'contract_date':     'Fecha de contrato',
            'installation_date': 'Fecha de instalación',
        }
        missing = [
            label
            for fname, label in field_labels.items()
            if not getattr(self, fname)
        ]
        if missing:
            raise ValidationError(
                "Los siguientes campos son obligatorios para continuar:\n"
                + "\n".join(f"• {m}" for m in missing)
            )
        if self.customer_type == 'company' and not self.vat:
            raise ValidationError("El NIT es obligatorio para empresas.")
        if self.customer_type == 'person' and not self.ci:
            raise ValidationError("El CI es obligatorio para personas naturales.")

    def _validate_signed_fields(self):
        if not self.contrato and not self.contract_attachment_ids:
            raise ValidationError(
                "Debe subir al menos un archivo del contrato (PDF, JPG o PNG) "
                "para registrar el contrato."
            )
        if self.contrato:
            self._validate_file_format()
        self._validate_attachment_files()

    def _validate_active_fields(self):
        missing = []
        if not self.location_link:
            missing.append('Link de Ubicación')
        if not self.coordinates:
            missing.append('Coordenadas')
        if missing:
            raise ValidationError(
                "Los siguientes campos son obligatorios para activar el contrato:\n"
                + "\n".join(f"• {m}" for m in missing)
            )

    def _validate_billing_fields(self):
        missing = []
        if not self.billing_name:
            missing.append('Nombre del facturante')
        if not self.billing_phone:
            missing.append('Teléfono del facturante')
        if not self.billing_ci:
            missing.append('CI del facturante')
        if missing:
            raise ValidationError(
                "Faltan datos del facturante:\n"
                + "\n".join(f"• {m}" for m in missing)
            )

    def _validate_terminated_fields(self):
        if not self.end_date:
            raise ValidationError(
                "El contrato finalizado debe tener una fecha de finalización."
            )

    def _validate_file_format(self):
        self._validate_binary_contract_file(self.contrato, self.contrato_filename, check_size=False)

    def _validate_binary_contract_file(self, contrato_binary, contrato_filename, check_size=True):
        if not contrato_binary:
            return

        filename = (contrato_filename or '').strip()
        if not filename:
            _logger.warning(
                "Contrato ID %s: archivo subido sin nombre; "
                "no se puede verificar el tipo MIME.", self.id
            )
        else:
            ext = os.path.splitext(filename.lower())[1]
            mime, _ = mimetypes.guess_type(filename.lower())
            if ext and ext not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"Formato de archivo no permitido: '{ext}'.\n"
                    "Solo se aceptan archivos PDF, JPG o PNG."
                )
            if mime and mime not in ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f"Tipo de archivo no permitido (MIME: {mime}).\n"
                    "Solo se aceptan PDF, JPG o PNG."
                )

        if check_size:
            self._validate_binary_contract_size(contrato_binary)

    def _validate_binary_contract_size(self, contrato_binary):
        if not contrato_binary:
            return
        try:
            file_bytes = base64.b64decode(contrato_binary)
            size = len(file_bytes)
        except Exception:
            _logger.warning(
                "Contrato ID %s: no se pudo decodificar el archivo para verificar tamaño.",
                self.id,
            )
            return
        if size > MAX_FILE_SIZE_BYTES:
            size_mb = size / (1024 * 1024)
            raise ValidationError(
                f"El archivo supera el tamaño máximo permitido de 5 MB "
                f"(tamaño actual: {size_mb:.2f} MB)."
            )

    def _validate_file_size(self):
        self._validate_binary_contract_size(self.contrato)

    def _validate_attachment_files(self):
        self._validate_attachment_recordset(self.contract_attachment_ids)

    def _validate_attachment_recordset(self, attachments):
        for attachment in attachments:
            if attachment.type and attachment.type != 'binary':
                raise ValidationError(
                    f"El archivo '{attachment.name}' no es un adjunto binario válido."
                )

            filename = (attachment.name or '').strip().lower()
            ext = os.path.splitext(filename)[1]
            mimetype = (attachment.mimetype or '').lower()

            if ext and ext not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"Formato de archivo no permitido: '{ext}'. "
                    "Solo se aceptan archivos PDF, JPG o PNG."
                )

            if mimetype and mimetype not in ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f"Tipo de archivo no permitido (MIME: {mimetype}). "
                    "Solo se aceptan PDF, JPG o PNG."
                )

            if attachment.file_size and attachment.file_size > MAX_FILE_SIZE_BYTES:
                size_mb = attachment.file_size / (1024 * 1024)
                raise ValidationError(
                    f"El archivo '{attachment.name}' supera el tamaño máximo permitido de 5 MB "
                    f"(tamaño actual: {size_mb:.2f} MB)."
                )

    def _get_contrato_url(self, download=False):
        self.ensure_one()
        if self.contract_attachment_ids:
            attachment = self.contract_attachment_ids.sorted('id', reverse=True)[0]
            return (
                f"/web/content?model=ir.attachment&id={attachment.id}"
                f"&field=datas&filename_field=name"
                f"&download={'true' if download else 'false'}"
            )

        if self.contrato:
            return (
                f"/web/content?model=customer.contract&id={self.id}"
                f"&field=contrato&filename_field=contrato_filename"
                f"&download={'true' if download else 'false'}"
            )

        raise UserError('No hay contrato adjunto para mostrar.')

    def _get_all_contract_attachments(self):
        self.ensure_one()
        return self.contract_attachment_ids

    def _open_attachment_selector_wizard(self, action_type='view'):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar archivo de contrato',
            'res_model': 'customer.contract.attachment.viewer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_action_type': action_type,
            },
        }

    def action_ver_contrato(self):
        self.ensure_one()
        if len(self._get_all_contract_attachments()) > 1:
            return self._open_attachment_selector_wizard(action_type='view')
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_contrato_url(download=False),
            'target': 'new',
        }

    def action_descargar_contrato(self):
        self.ensure_one()
        if len(self._get_all_contract_attachments()) > 1:
            return self._open_attachment_selector_wizard(action_type='download')
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_contrato_url(download=True),
            'target': 'self',
        }

    # =========================================================
    # GESTIÓN DE ESTADOS (BOTONES)
    # =========================================================
    def _change_state(self, new_state):
        self.write({'state': new_state})

    def action_set_pending(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(
                    f"Solo se puede enviar a 'Pendiente' desde 'Borrador'. "
                    f"Estado actual: {dict(record._fields['state'].selection).get(record.state)}"
                )
            record._validate_pending_fields()
        self._change_state('pending')

    def action_sign(self):
        for record in self:
            if record.state != 'pending':
                raise ValidationError(
                    "Solo se puede registrar el contrato desde el estado 'Pendiente'."
                )
            record._validate_pending_fields()
            record._validate_signed_fields()
            record._validate_billing_fields()
        self._change_state('signed')

    def action_activate(self):
        for record in self:
            if record.state != 'signed':
                raise ValidationError(
                    "El contrato debe estar en estado 'Contrato Registrado' para activarse."
                )
            record._validate_active_fields()
        self._change_state('active')

    def action_terminate(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != 'active':
                raise ValidationError(
                    "Solo se puede finalizar un contrato que esté 'Activo'."
                )
            if not record.termination_date:
                record.termination_date = today
        self._change_state('terminated')


# =========================================================
# WIZARD — Cambio de plan del contrato
# =========================================================
class CustomerContractPlanWizard(models.TransientModel):
    _name = 'customer.contract.plan.wizard'
    _description = 'Wizard para cambio de plan del contrato'

    contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato actual',
        required=True,
        readonly=True,
    )
    current_plan_id = fields.Many2one(
        'internet.plan',
        string='Plan actual',
        related='contract_id.plan_id',
        readonly=True,
    )
    current_price = fields.Float(
        string='Tarifa actual (Bs)',
        related='contract_id.plan_price',
        readonly=True,
    )
    new_plan_id = fields.Many2one(
        'internet.plan',
        string='Nuevo plan',
        required=True,
        domain="[('active', '=', True)]",
    )
    new_price = fields.Float(
        string='Tarifa nueva (Bs)',
        related='new_plan_id.price',
        readonly=True,
    )
    note = fields.Text(string='Motivo del cambio')
    contrato = fields.Binary(
        string='Archivo del Contrato',
        attachment=True,
    )
    contrato_filename = fields.Char(string='Nombre del archivo')
    contract_attachment_ids = fields.Many2many(
        'ir.attachment',
        'customer_contract_plan_wizard_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Archivos de contrato',
        help='Permite adjuntar múltiples archivos del contrato (PDF/JPG/PNG).',
    )

    def action_confirm(self):
        self.ensure_one()
        if self.new_plan_id == self.current_plan_id:
            raise ValidationError('Selecciona un plan diferente al actual.')

        if self.contrato:
            self.contract_id._validate_binary_contract_file(self.contrato, self.contrato_filename)
        if self.contract_attachment_ids:
            self.contract_id._validate_attachment_recordset(self.contract_attachment_ids)

        return self.contract_id.action_apply_plan_change(
            new_plan_id=self.new_plan_id.id,
            note=self.note or '',
            contrato=self.contrato,
            contrato_filename=self.contrato_filename or '',
            contract_attachment_ids=self.contract_attachment_ids.ids,
        )


class CustomerContractAttachmentViewerWizard(models.TransientModel):
    _name = 'customer.contract.attachment.viewer.wizard'
    _description = 'Seleccionar adjunto de contrato'

    contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato',
        required=True,
        readonly=True,
    )
    action_type = fields.Selection(
        [
            ('view', 'Ver en grande'),
            ('download', 'Descargar'),
        ],
        string='Acción',
        required=True,
        default='view',
        readonly=True,
    )
    available_attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_available_attachment_ids',
        string='Adjuntos disponibles',
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo',
        required=True,
        domain="[('id', 'in', available_attachment_ids)]",
    )

    @api.depends('contract_id')
    def _compute_available_attachment_ids(self):
        for rec in self:
            rec.available_attachment_ids = rec.contract_id._get_all_contract_attachments()
            if not rec.attachment_id and rec.available_attachment_ids:
                rec.attachment_id = rec.available_attachment_ids.sorted('id', reverse=True)[0]

    def action_confirm(self):
        self.ensure_one()
        if not self.attachment_id:
            raise UserError('Debes seleccionar un archivo.')

        return {
            'type': 'ir.actions.act_url',
            'url': (
                f"/web/content?model=ir.attachment&id={self.attachment_id.id}"
                f"&field=datas&filename_field=name"
                f"&download={'true' if self.action_type == 'download' else 'false'}"
            ),
            'target': 'self' if self.action_type == 'download' else 'new',
        }
