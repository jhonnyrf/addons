# -*- coding: utf-8 -*-
import base64
from datetime import date
from calendar import monthrange
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class WigoPagoEstado(models.Model):
    """
    Registro de pago mensual por cliente.
    Reemplaza el Excel de Dania sin tocar el sistema contable SIN/SIAT.
    Una fila = un mes de un cliente.
    """
    _name = 'wigo.pago.estado'
    _description = 'Registro de Pago Mensual del Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anio desc, mes desc, partner_id'
    _rec_name = 'display_name'
    
    eligible_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_eligible_partner_ids',
        string='Clientes con contrato activo',
        store=False,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict', tracking=True, index=True,
        domain="[('id', 'in', eligible_partner_ids)]",
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
        domain="[('partner_id', '=', partner_id), ('state', '=', 'active')]",
        tracking=True,
        required=True,
    )
    client_service_id = fields.Many2one(
        'wigo.ftth.client.service', string='Servicio (CF)',
        domain="[('partner_id', '=', partner_id)]",
        ondelete='restrict', tracking=True, index=True,
    )
    codigo_cliente = fields.Char(string='Código CF', compute='_compute_contract_service_data', store=True, readonly=True)
    plan_id = fields.Many2one('internet.plan', string='Plan', compute='_compute_contract_service_data', store=True, readonly=True)
    partner_ci = fields.Char(string='CI', compute='_compute_partner_snapshot', store=False)
    partner_celular = fields.Char(string='Celular', compute='_compute_partner_snapshot', store=False)
    partner_telefono = fields.Char(string='Teléfono', compute='_compute_partner_snapshot', store=False)
    partner_email = fields.Char(string='Correo', compute='_compute_partner_snapshot', store=False)
    partner_direccion = fields.Char(string='Dirección', compute='_compute_partner_snapshot', store=False)
    contract_state = fields.Selection(
        related='contract_id.state',
        string='Estado de contrato',
        readonly=True,
        store=False,
    )
    crm_lead_id = fields.Many2one(
        'crm.lead', string='Lead CRM',
        compute='_compute_crm_data', store=False, readonly=True,
    )
    crm_zona = fields.Char(string='Zona CRM', compute='_compute_crm_data', store=False)
    crm_direccion = fields.Char(string='Dirección CRM', compute='_compute_crm_data', store=False)
    crm_ubicacion = fields.Char(string='Ubicación CRM', compute='_compute_crm_data', store=False)
    crm_coordenadas = fields.Char(string='Coordenadas CRM', compute='_compute_crm_data', store=False)

    
    anio = fields.Char(
        string='Año', required=True,
    )
    anio_display = fields.Char(
        string='Año',
        compute='_compute_anio_display',
        store=False,
        readonly=True,
    )
    mes = fields.Selection(
        [(str(i), name) for i, name in enumerate([
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
        ], start=0) if i > 0],
        string='Mes', required=True,
    )
    periodo = fields.Char(
        string='Período', compute='_compute_periodo', store=True,
    )

    
    monto_plan = fields.Float(
        string='Monto del plan (Bs)',
        related='plan_id.price', store=True, readonly=True,
    )
    payment_mode = fields.Selection(
        [
            ('prepaid', 'Prepago'),
            ('postpaid', 'Postpago'),
        ],
        string='Modalidad de pago',
        compute='_compute_payment_mode',
        store=True,
        readonly=True,
        help='Modalidad copiada automáticamente desde el contrato relacionado.',
    )
    monto_prorrateo = fields.Float(
        string='Monto prorrateo (Bs)',
        default=0.0,
        help='Monto editable manualmente cuando el tipo de ajuste habilita prorrateo.',
    )
    tipo_ajuste_id = fields.Many2one(
        'wigo.cobranza.tipo_ajuste',
        string='Tipo de ajuste',
        ondelete='restrict',
        tracking=True,
    )
    tipo_ajuste_is_default = fields.Boolean(
        related='tipo_ajuste_id.is_default',
        string='Tipo de ajuste por defecto',
        readonly=True,
        store=False,
    )
    tipo_ajuste_enable_proration = fields.Boolean(
        related='tipo_ajuste_id.enable_proration',
        string='Tipo habilita prorrateo',
        readonly=True,
        store=False,
    )
    tipo_ajuste_requires_reason = fields.Boolean(
        related='tipo_ajuste_id.requires_reason',
        string='Tipo requiere motivo',
        readonly=True,
        store=False,
    )
    tipo_ajuste_color = fields.Integer(
        related='tipo_ajuste_id.color',
        string='Color de tipo de ajuste',
        readonly=True,
        store=False,
    )
    es_primer_mes = fields.Boolean(
        string='¿Es primer mes?',
        default=False,
        help='Compatibilidad con registros históricos. No usar para nueva lógica.',
    )
    motivo = fields.Text(
        string='Motivo',
        help='Justificación del ajuste aplicado al cobro.',
    )
    monto_a_cobrar = fields.Float(
        string='Monto a cobrar (Bs)',
        compute='_compute_monto_a_cobrar', store=True,
        inverse='_inverse_monto_a_cobrar',
        help='Prorrateo si es primer mes, tarifa completa en el resto.',
    )
    monto_a_cobrar_manual = fields.Float(
        string='Monto a cobrar manual (Bs)',
        default=False,
        copy=False,
        help='Sobrescribe el monto a cobrar sugerido por el sistema.',
    )
    monto_a_cobrar_manual_aplicado = fields.Boolean(
        string='Override de monto a cobrar aplicado',
        default=False,
        copy=False,
    )
    monto_pagado = fields.Float(
        string='Monto pagado (Bs)', tracking=True,
    )
    diferencia = fields.Float(
        string='Diferencia (Bs)',
        compute='_compute_diferencia', store=True,
    )

    
    fecha_pago = fields.Date(
        string='Fecha de pago',
        tracking=True,
        default=lambda self: fields.Date.context_today(self),
    )
    canal_pago = fields.Selection([
        ('qr',           'QR bancario'),
        ('transferencia','Transferencia bancaria'),
        ('efectivo',     'Efectivo en oficina'),
    ], string='Canal de pago', tracking=True)
    comprobante = fields.Char(string='Referencia / N° comprobante', tracking=True)
    comprobante_adjunto = fields.Binary(string='Comprobante (imagen o PDF)')
    comprobante_adjunto_fname = fields.Char()
    comprobante_attachment_ids = fields.Many2many(
        'ir.attachment',
        'wigo_pago_estado_attachment_rel',
        'pago_id',
        'attachment_id',
        string='Comprobantes adjuntos',
        copy=False,
    )
    comprobante_adjunto_is_image = fields.Boolean(
        string='Adjunto es imagen', compute='_compute_comprobante_adjunto_type', store=False,
    )
    comprobante_adjunto_is_pdf = fields.Boolean(
        string='Adjunto es PDF', compute='_compute_comprobante_adjunto_type', store=False,
    )
    has_comprobante = fields.Boolean(
        string='Tiene comprobante', compute='_compute_has_comprobante', store=False,
    )
    registrado_por = fields.Many2one(
        'res.users', string='Registrado por',
        default=lambda self: self.env.user, tracking=True,
    )
    contabilidad_editable = fields.Boolean(
        string='Modo edición contable',
        compute='_compute_contabilidad_editable',
        store=False,
    )

    
    estado_pago = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('mora', 'Mora'),
    ], string='Estado de pago', default='pendiente',
       required=True, tracking=True, index=True,
    )
    fecha_vencimiento = fields.Date(
        string='Fecha de vencimiento',
        compute='_compute_fecha_vencimiento', store=True,
        help='Último día del mes facturado. Se usa para calcular días de atraso.',
    )
    dias_atraso = fields.Integer(
        string='Días de atraso',
        compute='_compute_dias_atraso', store=False,
        help='Días transcurridos desde la fecha de vencimiento.',
    )
    
    notas = fields.Text(string='Notas de cobranza')
    justificacion_edicion = fields.Text(string='Justificación de edición contable')

    # ── Display ───────────────────────────────────────────────────
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('comprobante_adjunto', 'comprobante_attachment_ids')
    def _compute_has_comprobante(self):
        for rec in self:
            rec.has_comprobante = bool(rec.comprobante_adjunto or rec.comprobante_attachment_ids)

    @api.depends_context('contabilidad_editable')
    def _compute_contabilidad_editable(self):
        editable = bool(self.env.context.get('contabilidad_editable'))
        for rec in self:
            rec.contabilidad_editable = editable

    # ─────────────────────────────────────────────────────────────
    # Constraints (Odoo 19: @api.constrains en lugar de _sql_constraints)
    # ─────────────────────────────────────────────────────────────
    @api.constrains('contract_id', 'client_service_id', 'plan_id', 'mes', 'anio')
    def _check_unique_cliente_periodo(self):
        for rec in self:
            if not rec.contract_id and not rec.client_service_id:
                continue

            domain = [
                ('mes', '=', rec.mes),
                ('anio', '=', rec.anio),
                ('plan_id', '=', rec.plan_id.id),
                ('id', '!=', rec.id),
            ]

            if rec.contract_id:
                domain.append(('contract_id', '=', rec.contract_id.id))
            else:
                domain.append(('client_service_id', '=', rec.client_service_id.id))

            duplicado = self.search(domain, limit=1)

            if duplicado:
                periodo_txt = rec.periodo or (
                    f"{dict(self._fields['mes'].selection).get(rec.mes, '')} {rec.anio}".strip()
                    if rec.mes and rec.anio else ''
                )

                raise ValidationError(
                    f'Ya existe un registro de pago para '
                    f'{rec.codigo_cliente} '
                    f'con el plan {rec.plan_id.display_name} '
                    f'en el periodo {periodo_txt}.'
                )

    @api.constrains('partner_id')
    def _check_partner_has_contract(self):
        Contract = self.env['customer.contract']
        for rec in self:
            if not rec.partner_id:
                continue
            has_contract = Contract.search_count([
                ('partner_id', '=', rec.partner_id.id),
                ('state', '=', 'active'),
            ])
            if not has_contract:
                raise ValidationError(
                    f"El cliente '{rec.partner_id.name}' no tiene contrato activo."
                )

    # ─────────────────────────────────────────────────────────────
    # Computes
    # ─────────────────────────────────────────────────────────────
    @api.depends('anio', 'mes')
    def _compute_periodo(self):
        for rec in self:
            if rec.mes and rec.anio:
                month_name = dict(self._fields['mes'].selection).get(rec.mes, '')
                rec.periodo = f"{month_name} {rec.anio}".strip()
            else:
                rec.periodo = ''

    def _suggest_next_period_values(self, contract=None, client_service=None, partner=None):
        domain = []
        if contract:
            domain.append(('contract_id', '=', contract.id))
        elif client_service:
            domain.append(('client_service_id', '=', client_service.id))
        elif partner:
            domain.append(('partner_id', '=', partner.id))

        if not domain:
            return str(date.today().month), date.today().year

        records = self.search(domain)
        if not records:
            return str(date.today().month), date.today().year

        last_record = max(
            records,
            key=lambda rec: (int(rec.anio or 0), int(rec.mes or 0), rec.id or 0),
        )
        mes_actual = int(last_record.mes or date.today().month)
        anio_actual = int(last_record.anio or date.today().year)
        if mes_actual >= 12:
            return '1', anio_actual + 1
        return str(mes_actual + 1), anio_actual

    def _apply_next_period_for_new_record(self):
        for rec in self:
            if rec.id:
                continue
            mes_sugerido, anio_sugerido = rec._suggest_next_period_values(
                contract=rec.contract_id,
                client_service=rec.client_service_id,
                partner=rec.partner_id,
            )
            rec.mes = mes_sugerido
            rec.anio = anio_sugerido

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        tipo_ajuste = self._get_default_tipo_ajuste()
        if 'tipo_ajuste_id' in fields_list and not res.get('tipo_ajuste_id') and tipo_ajuste:
            res['tipo_ajuste_id'] = tipo_ajuste.id
        if 'monto_prorrateo' in fields_list and 'monto_prorrateo' not in res:
            res['monto_prorrateo'] = 0.0
        if 'motivo' in fields_list and 'motivo' not in res:
            res['motivo'] = False

        if tipo_ajuste:
            res['es_primer_mes'] = bool(tipo_ajuste.enable_proration)
            if not tipo_ajuste.enable_proration:
                res['monto_prorrateo'] = 0.0
            if not tipo_ajuste.requires_reason:
                res['motivo'] = False

        contract_id = res.get('contract_id') or self.env.context.get('default_contract_id')
        service_id = res.get('client_service_id') or self.env.context.get('default_client_service_id')
        partner_id = res.get('partner_id') or self.env.context.get('default_partner_id')

        if not contract_id and partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            contract = self._get_preferred_contract(partner)
            if contract:
                contract_id = contract.id
                if 'contract_id' in fields_list:
                    res['contract_id'] = contract.id

        if (not service_id) and contract_id:
            contract = self.env['customer.contract'].browse(contract_id)
            service = self._find_client_service_for_contract(contract)
            if service:
                service_id = service.id
                if 'client_service_id' in fields_list:
                    res['client_service_id'] = service.id

        if ('mes' in fields_list and not res.get('mes')) or ('anio' in fields_list and not res.get('anio')):
            mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                contract=self.env['customer.contract'].browse(contract_id) if contract_id else None,
                client_service=self.env['wigo.ftth.client.service'].browse(service_id) if service_id else None,
                partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
            )
            if 'mes' in fields_list and not res.get('mes'):
                res['mes'] = mes_sugerido
            if 'anio' in fields_list and not res.get('anio'):
                res['anio'] = anio_sugerido

        if tipo_ajuste and tipo_ajuste.is_default and contract_id:
            contract = self.env['customer.contract'].browse(contract_id)
            res['monto_a_cobrar_manual'] = 0.0
            res['monto_a_cobrar_manual_aplicado'] = False
            res['monto_pagado'] = contract.plan_id.price if contract.plan_id else 0.0

        return res

    def _get_default_tipo_ajuste(self):
        TipoAjuste = self.env['wigo.cobranza.tipo_ajuste']
        return TipoAjuste.search([
            ('active', '=', True),
            ('is_default', '=', True),
        ], limit=1) or TipoAjuste.search([
            ('active', '=', True),
        ], order='id asc', limit=1)

    def _get_legacy_proration_tipo_ajuste(self):
        return self.env['wigo.cobranza.tipo_ajuste'].search([
            ('active', '=', True),
            ('enable_proration', '=', True),
        ], order='is_default desc, id asc', limit=1)

    def _sync_payment_defaults(self):
        # Avoid recursive ORM writes: update only the necessary columns directly
        # and invalidate the cache so the record reflects the new values.
        # Skip for unsaved (NewId) records; onchange only needs field updates.
        if not self:
            return

        table = self._table
        for rec in self:
            # Only update DB for persisted records (id is int, not NewId)
            if not isinstance(rec.id, int):
                continue

            updates = []
            params = []

            if rec.tipo_ajuste_id and rec.tipo_ajuste_id.is_default:
                if rec.monto_pagado != rec.monto_a_cobrar:
                    updates.append('monto_pagado = %s')
                    params.append(rec.monto_a_cobrar or 0.0)
            elif rec.monto_pagado in (False, None):
                updates.append('monto_pagado = %s')
                params.append(0.0)

            if rec.tipo_ajuste_id:
                expected_primer = bool(rec.tipo_ajuste_id.enable_proration)
                if rec.es_primer_mes != expected_primer:
                    updates.append('es_primer_mes = %s')
                    params.append(expected_primer)
                if not rec.tipo_ajuste_id.enable_proration and rec.monto_prorrateo not in (False, 0.0):
                    updates.append('monto_prorrateo = %s')
                    params.append(0.0)
                if not rec.tipo_ajuste_id.requires_reason and rec.motivo:
                    updates.append('motivo = %s')
                    params.append(False)

            if not updates:
                continue

            params.append(rec.id)
            query = 'UPDATE %s SET %s WHERE id = %%s' % (table, ', '.join(updates))
            self.env.cr.execute(query, params)
            rec._invalidate_cache(['monto_pagado', 'es_primer_mes', 'monto_prorrateo', 'motivo'])
            rec.modified(['monto_pagado', 'es_primer_mes', 'monto_prorrateo', 'motivo'])

    def _apply_default_amounts_onchange(self):
        """Ajusta los montos en memoria para formularios nuevos o en edición."""
        for rec in self:
            if not rec.tipo_ajuste_id:
                continue

            if rec.tipo_ajuste_id.is_default:
                rec.monto_a_cobrar_manual = 0.0
                rec.monto_a_cobrar_manual_aplicado = False
                rec.es_primer_mes = False
                rec.monto_prorrateo = 0.0
                rec.monto_a_cobrar = rec.monto_plan or 0.0
                rec.monto_pagado = rec.monto_a_cobrar or 0.0
                continue

            if not rec.monto_pagado:
                rec.monto_pagado = rec.monto_a_cobrar or rec.monto_plan or 0.0

    def _compute_eligible_partner_ids(self):
        Contract = self.env['customer.contract']
        partner_ids = Contract.search([
            ('state', '=', 'active'),
        ]).mapped('partner_id').ids
        for rec in self:
            rec.eligible_partner_ids = [(6, 0, partner_ids)]

    @api.depends('contract_id.name', 'contract_id.plan_id', 'client_service_id.codigo_cliente', 'client_service_id.plan_id')
    def _compute_contract_service_data(self):
        for rec in self:
            rec.codigo_cliente = rec.contract_id.name or rec.client_service_id.codigo_cliente or False
            rec.plan_id = rec.contract_id.plan_id or rec.client_service_id.plan_id or False

    @api.depends('contract_id.payment_mode')
    def _compute_payment_mode(self):
        for rec in self:
            rec.payment_mode = rec.contract_id.payment_mode if rec.contract_id else False

    @api.depends('partner_id')
    def _compute_partner_snapshot(self):
        for rec in self:
            partner = rec.partner_id
            rec.partner_ci = (getattr(partner, 'ci', False) or False) if partner else False
            rec.partner_celular = (
                getattr(partner, 'celular', False) or
                getattr(partner, 'mobile', False) or
                getattr(partner, 'phone', False) or
                False
            ) if partner else False
            rec.partner_telefono = getattr(partner, 'phone', False) if partner else False
            rec.partner_email = partner.email if partner else False
            rec.partner_direccion = (
                getattr(partner, 'direccion', False) or partner.street or False
            ) if partner else False

    @api.depends(
        'tipo_ajuste_id',
        'tipo_ajuste_id.enable_proration',
        'monto_prorrateo',
        'monto_plan',
        'monto_a_cobrar_manual',
        'monto_a_cobrar_manual_aplicado',
        'es_primer_mes',
    )
    def _compute_monto_a_cobrar(self):
        for rec in self:
            if rec.monto_a_cobrar_manual_aplicado:
                rec.monto_a_cobrar = rec.monto_a_cobrar_manual
            elif rec.tipo_ajuste_id:
                rec.monto_a_cobrar = rec.monto_prorrateo if rec.tipo_ajuste_id.enable_proration else rec.monto_plan
                rec.monto_pagado = rec.monto_prorrateo if rec.tipo_ajuste_id.enable_proration else rec.monto_plan
            elif rec.es_primer_mes:
                rec.monto_a_cobrar = rec.monto_prorrateo
            else:                                
                rec.monto_a_cobrar = rec.monto_plan

    def _inverse_monto_a_cobrar(self):
        for rec in self:
            rec.monto_a_cobrar_manual = rec.monto_a_cobrar
            rec.monto_a_cobrar_manual_aplicado = True

    @api.onchange('tipo_ajuste_id', 'es_primer_mes', 'monto_prorrateo', 'monto_plan')
    def _onchange_prorrateo_manual(self):
        for rec in self:
            if rec.tipo_ajuste_id:
                rec.es_primer_mes = bool(rec.tipo_ajuste_id.enable_proration)
                if not rec.tipo_ajuste_id.enable_proration:
                    rec.monto_prorrateo = 0.0
                if not rec.tipo_ajuste_id.requires_reason:
                    rec.motivo = False
            elif not rec.es_primer_mes:
                rec.monto_prorrateo = 0.0
            # Primero calcular el monto a cobrar (ya muestra correctamente en la vista)
            #rec.monto_a_cobrar = rec.monto_prorrateo if (rec.tipo_ajuste_id and rec.tipo_ajuste_id.enable_proration) or rec.es_primer_mes else rec.monto_plan
            rec.monto_a_cobrar = rec.monto_prorrateo if (rec.tipo_ajuste_id and rec.tipo_ajuste_id.enable_proration) or rec.es_primer_mes else rec.monto_plan
            _logger.info(f"Onchange tipo_ajuste_id: recalculando monto_a_cobrar={rec.monto_a_cobrar} para pago {rec.id} (ajuste: {rec.tipo_ajuste_id.name if rec.tipo_ajuste_id else 'N/A'}, es_primer_mes: {rec.es_primer_mes}, monto_prorrateo: {rec.monto_prorrateo}, monto_plan: {rec.monto_plan})")
            # Sincronizar el monto pagado con el monto a cobrar por defecto
            # (esto asegura que al seleccionar un tipo con prorrateo el campo 'monto_pagado'
            # se actualice inmediatamente en la vista al mismo valor que se mostrará en
            # 'monto_a_cobrar').
            rec.monto_pagado = rec.monto_a_cobrar or 0.0
            _logger.info(f"Onchange tipo_ajuste_id: recalculando monto_pagado={rec.monto_pagado} para pago {rec.id} (ajuste: {rec.tipo_ajuste_id.name if rec.tipo_ajuste_id else 'N/A'}, es_primer_mes: {rec.es_primer_mes}, monto_prorrateo: {rec.monto_prorrateo}, monto_plan: {rec.monto_plan})")
            

            self._apply_default_amounts_onchange()

    @api.constrains('tipo_ajuste_id', 'monto_prorrateo', 'motivo')
    def _check_tipo_ajuste_rules(self):
        for rec in self:
            ajuste = rec.tipo_ajuste_id
            if not ajuste:
                continue
            if ajuste.requires_reason and not (rec.motivo or '').strip():
                raise ValidationError('El tipo de ajuste seleccionado requiere un motivo.')
            if not ajuste.enable_proration and rec.monto_prorrateo not in (False, 0.0):
                raise ValidationError('El tipo de ajuste seleccionado no permite prorrateo.')

    @api.depends('monto_a_cobrar', 'monto_pagado','monto_prorrateo')
    def _compute_diferencia(self):
        for rec in self:
            rec.diferencia = rec.monto_pagado - rec.monto_a_cobrar

    @api.depends('comprobante_adjunto', 'comprobante_adjunto_fname')
    def _compute_comprobante_adjunto_type(self):
        for rec in self:
            name = (rec.comprobante_adjunto_fname or '').lower()
            is_image = bool(name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')))
            is_pdf = name.endswith('.pdf')

            # Fallback when filename is missing: detect by file signature in base64 payload.
            if rec.comprobante_adjunto and not (is_image or is_pdf):
                try:
                    raw = base64.b64decode(rec.comprobante_adjunto)
                    if raw.startswith(b'%PDF'):
                        is_pdf = True
                    elif (
                        raw.startswith(b'\xff\xd8\xff') or
                        raw.startswith(b'\x89PNG\r\n\x1a\n') or
                        raw.startswith(b'GIF87a') or
                        raw.startswith(b'GIF89a') or
                        raw.startswith(b'RIFF')
                    ):
                        is_image = True
                except Exception:
                    # Keep both flags false if payload cannot be decoded.
                    pass

            rec.comprobante_adjunto_is_image = is_image
            rec.comprobante_adjunto_is_pdf = is_pdf

    # ── Fecha vencimiento y días de atraso ─────────────────────
    @api.depends('anio', 'mes', 'contract_id')
    def _compute_fecha_vencimiento(self):
        """
                Calcula la fecha efectiva en la que el registro entra en mora.

                La regla se aplica desde el primer día del período facturado:
                - Para meses: 1er día del período + meses_mora
                    Ej: Abril + 1 mes = 1 de Mayo
                - Para días: 1er día del período + días_mora
                    Ej: 1 de Abril + 15 días = 16 de Abril
        """
        for rec in self:
            if not rec.anio or not rec.mes:
                rec.fecha_vencimiento = False
                continue

            try:
                mes_int = int(rec.mes)
                anio_int = int(rec.anio)
                fecha_inicio_periodo = date(anio_int, mes_int, 1)

                # Si no hay contrato, fallback al primer día del período
                if not rec.contract_id:
                    rec.fecha_vencimiento = fecha_inicio_periodo
                    continue

                regla = rec._get_regla_for_contract(rec.contract_id)
                if not regla:
                    # Sin regla, usar primer día del período
                    rec.fecha_vencimiento = fecha_inicio_periodo
                    continue

                rec.fecha_vencimiento = self._calculate_fecha_vencimiento(
                    mes_int,
                    anio_int,
                    regla,
                )

            except Exception as e:
                _logger.warning(f"Error calculando fecha_vencimiento para pago {rec.id}: {e}")
                rec.fecha_vencimiento = False

    def _compute_dias_atraso(self):
        """Días transcurridos desde la fecha de vencimiento."""
        hoy = date.today()
        for rec in self:
            if rec.fecha_vencimiento and rec.estado_pago not in ('pagado',):
                delta = (hoy - rec.fecha_vencimiento).days
                rec.dias_atraso = max(delta, 0)
            else:
                rec.dias_atraso = 0

    def _get_regla_for_contract(self, contract):
        """Devuelve la regla aplicable para un contrato según su modalidad."""
        Regla = self.env['wigo.cobranza.regla']                    
        if not contract:
            return Regla        
        return Regla.search([
            ('active', '=', True),
            ('payment_mode', 'in', [contract.payment_mode, 'all']),
        ], order='sequence, id', limit=1)

    def _get_existing_payment_for_period(self, contract=None, client_service=None, partner=None, mes=None, anio=None):
        """
        Busca un cobro ya existente para evitar duplicados por período.
        
        IMPORTANTE: Busca por período facturado (mes/anio), no por fecha actual.
        Esto es correcto porque el período se calcula basado en dia_generacion,
        no en la fecha del cron.
        """
        domain = []
        if mes is not None:
            domain.append(('mes', '=', str(mes)))
        if anio is not None:
            domain.append(('anio', '=', int(anio)))

        if contract:
            domain.append(('contract_id', '=', contract.id))
        elif client_service:
            domain.append(('client_service_id', '=', client_service.id))
        elif partner:
            domain.append(('partner_id', '=', partner.id))
        else:
            return self.browse()

        return self.search(domain, limit=1, order='id desc')

    def _months_overdue(self, rec, today=None):
        today = today or date.today()
        if not rec or not rec.fecha_vencimiento:
            return 0
        due = rec.fecha_vencimiento
        months = (today.year - due.year) * 12 + (today.month - due.month)
        if today.day < due.day:
            months -= 1
        return max(months, 0)

    def _months_between_dates(self, start_date, end_date=None):
        """
        Calcula meses completos transcurridos entre `start_date` y `end_date`.
        Ej: start=2026-04-30, end=2026-05-30 -> 1
        start=2026-04-30, end=2026-05-29 -> 0
        """
        end_date = end_date or date.today()
        if not start_date:
            return 0
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if end_date.day < start_date.day:
            months -= 1
        return max(months, 0)

    def _get_active_contracts_for_rule(self, rule):
        """Contratos activos que pueden ser impactados por una regla."""
        Contract = self.env['customer.contract']
        domain = [('state', '=', 'active')]
        if rule.payment_mode and rule.payment_mode != 'all':
            domain.append(('payment_mode', '=', rule.payment_mode))
        return Contract.search(domain, order='partner_id, id')

    def _add_months_to_date(self, base_date, months_to_add):
        """
        Suma meses a una fecha, manejando correctamente cambios de año y
        ajustando el día si el mes destino tiene menos días.
        
        Ejemplo:
        - 2026-01-31 + 1 mes = 2026-02-28 (febrero tiene solo 28 días)
        - 2026-01-31 + 2 meses = 2026-03-31 (marzo tiene 31 días)
        """
        from calendar import monthrange
        
        month = base_date.month + months_to_add
        year = base_date.year
        
        # Ajustar año si pasamos los 12 meses
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        
        # Asegurar que el día existe en el mes destino
        # Si no existe, usar el último día del mes
        _, max_day = monthrange(year, month)
        day = min(base_date.day, max_day)
        
        return date(year, month, day)

    def _calculate_billed_period_from_trigger_day(self, rule, today=None):
        """
        Calcula el período facturado basado en dia_generacion de la regla.
        
        Ejemplo:
        - Hoy es 7 de mayo (today.day=7)
        - dia_generacion=5
        - Como 5 <= 7, generamos factura para MAYO (mes actual)
        
        Otro ejemplo:
        - Hoy es 3 de mayo (today.day=3)
        - dia_generacion=5
        - Como 5 > 3, generamos factura para ABRIL (mes anterior)
        
        Retorna: (mes_int, año_int)
        """
        today = today or date.today()
        trigger_day = int(rule.dia_generacion)
        current_day = today.day
        current_month = today.month
        current_year = today.year

        # Si el día actual es >= al día de generación, generamos para este mes
        if current_day >= trigger_day:
            return current_month, current_year

        # Si el día actual es < al día de generación, generamos para el mes anterior
        if current_month == 1:
            return 12, current_year - 1
        return current_month - 1, current_year
    def _get_fecha_inicio_periodo(self, mes_facturado, anio_facturado):
        """
        Obtiene el primer día del período facturado.

        Ejemplo:
        - mes=4, año=2026
        - retorna: 2026-04-01
        """

        try:
            mes_int = int(mes_facturado)
            anio_int = int(anio_facturado)

            fecha_inicio = date(anio_int, mes_int, 1)

            _logger.info(
                f"Fecha inicio período: {fecha_inicio} "
                f"para mes {mes_int} y año {anio_int}"
            )

            return fecha_inicio

        except Exception as e:
            _logger.error(f"Error al obtener fecha inicio período: {e}")
            return False
    def _calculate_fecha_vencimiento(self, mes_facturado, anio_facturado, rule):
        """
        Calcula la fecha efectiva de mora a partir del inicio del período.
        """

        try:
            fecha_inicio_periodo = self._get_fecha_inicio_periodo(
                mes_facturado,
                anio_facturado
            )

            if not fecha_inicio_periodo:
                return False

            # Mora por meses
            if rule.mora_criterio == 'meses':
                meses_a_agregar = int(rule.meses_mora or 0)

                fecha_vencimiento = self._add_months_to_date(
                    fecha_inicio_periodo,
                    meses_a_agregar
                )

            # Mora por días
            else:
                dias_a_agregar = int(rule.dias_mora or 0)

                fecha_vencimiento = (
                    fecha_inicio_periodo +
                    timedelta(days=dias_a_agregar)
                )

            _logger.info(f"Fecha vencimiento: {fecha_vencimiento}")

            return fecha_vencimiento

        except Exception as e:
            _logger.error(f"Error al calcular fecha_vencimiento: {e}")
            return False

    def _build_generation_vals(self, contract, rule, today):
        """
        Valores mínimos para crear un cobro mensual automático.
        
        IMPORTANTE: El período facturado se calcula basado en dia_generacion,
        NO en la fecha actual del cron. Esto asegura que siempre se genere
        la factura para el período correcto independientemente de cuándo
        se ejecute el cron.
        
        La fecha_vencimiento se calcula automáticamente basada en:
        - Último día del período facturado
        - Configuración de mora (dias_mora o meses_mora)
        """
        service = self._find_client_service_for_contract(contract)
        
        # Calcular período facturado basado en dia_generacion
        mes_facturado, anio_facturado = self._calculate_billed_period_from_trigger_day(rule, today)
        
        # Calcular fecha_vencimiento de forma automática
        fecha_vencimiento = self._calculate_fecha_vencimiento(
            mes_facturado, anio_facturado, rule
        )
        
        vals = {
            'partner_id': contract.partner_id.id,
            'contract_id': contract.id,
            'mes': str(mes_facturado),
            'anio': anio_facturado,
            'estado_pago': rule.estado_inicial,
            'fecha_pago': fields.Date.context_today(self),
        }
        
        # Establecer fecha_vencimiento calculada si es válida
        # (se sobrescribirá automáticamente cuando mes/anio cambien)
        if fecha_vencimiento:
            # Nota: No almacenamos esto directamente porque fecha_vencimiento
            # es un computed field que se recalcula automáticamente.
            # Sin embargo, podemos dejar un log para debugging.
            _logger.info(
                f"Período: {mes_facturado}/{anio_facturado}, "
                f"fecha_vencimiento calculada: {fecha_vencimiento}"
            )
        
        if service:
            vals['client_service_id'] = service.id
        return vals

    def _notify_cobranza_group(self, body, model='wigo.pago.estado', res_id=False):
        group = self.env.ref('wigo_cobranza.group_cobranza', raise_if_not_found=False)
        if not group:
            return
        partners = group.user_ids.mapped('partner_id')
        if not partners:
            return
        self.env['mail.message'].create({
            'message_type': 'notification',
            'body': body,
            'partner_ids': partners.ids,
            'model': model,
            'res_id': res_id,
        })

    def _deactivate_legacy_crons(self):
        """Desactiva crons antiguos que apuntaban a procesos hardcodeados."""
        cron_xmlids = [
            'wigo_cobranza.cron_alertar_mora_dia1',
            'wigo_cobranza.cron_evaluar_cobranza',
            'wigo_cobranza.cron_detectar_incobrables',
            'wigo_cobranza.cron_alertar_suspension',
        ]
        crons = self.env['ir.cron'].sudo()
        for xmlid in cron_xmlids:
            cron = self.env.ref(xmlid, raise_if_not_found=False)
            if cron and cron.active:
                crons.browse(cron.id).write({'active': False})

    def _cron_generar_deudas_diarias(self, today=None):
        today = today or date.today()
        rules = self.env['wigo.cobranza.regla']._get_generation_rules_for_day(today.day)
        if not rules:
            return 0

        created = 0
        seen_contracts = set()
        for rule in rules:
            contracts = self._get_active_contracts_for_rule(rule)
            # Calcular el período que esta regla va a facturar
            mes_facturado, anio_facturado = self._calculate_billed_period_from_trigger_day(rule, today)

            for contract in contracts:
                if contract.id in seen_contracts:
                    continue
                seen_contracts.add(contract.id)

                existing = self._get_existing_payment_for_period(
                    contract=contract,
                    mes=str(mes_facturado),
                    anio=anio_facturado,
                )
                if existing:
                    continue

                vals = self._build_generation_vals(contract, rule, today)
                self.create(vals)
                created += 1

        if created:
            self._notify_cobranza_group(
                f"Se generaron {created} registros de cobro pendientes "
                f"para el período {today.strftime('%B %Y')}. Por favor inicie la gestión de cobro."
            )
        return created

    def _get_open_payments_for_rules_mora(self, today=None):
        today = today or date.today()
        return self.search([
            ('estado_pago', 'in', ['pendiente', 'mora']),
            ('contract_id', '!=', False),
        ], order='fecha_vencimiento asc, id asc')
    def _get_open_payments_for_rules_incobrables(self, today=None):
        today = today or date.today()
        return self.search([
            ('estado_pago', 'in',  ['mora']),
            ('contract_id', '!=', False),
        ], order='fecha_vencimiento asc, id asc')    

    def _cron_evaluar_mora_diaria(self, today=None):
        today = today or date.today()
        pagos = self._get_open_payments_for_rules_mora(today)        
        mora_count = 0        
        for rec in pagos:
            regla = self._get_regla_for_contract(rec.contract_id)
            
            if not regla:
                continue
            # Calcular la fecha en la que este registro entra en mora
            overdue_date = self._calculate_fecha_vencimiento(rec.mes, rec.anio, regla)
            
            if not overdue_date:
                continue
            supera_mora = today >= overdue_date

            if not supera_mora:
                continue

            if rec.estado_pago != 'mora':
                rec.write({'estado_pago': 'mora'})
                mora_count += 1
                self._notify_mora(rec, regla)            

        return mora_count

    def _cron_evaluar_incobrables_diario(self, today=None):

        today = today or date.today()

        _logger.info(
            f"Evaluando incobrables para pagos abiertos a fecha {today}"
        )

        pagos = self._get_open_payments_for_rules_incobrables(today)

        contracts_to_check = set()

        contracts = pagos.mapped('contract_id')

        for contract in contracts:

            regla = self._get_regla_for_contract(contract)

            if not regla:
                continue

            # ==================================================
            # CRITERIO POR "MESES"
            # ==================================================
            # En este caso:
            #
            # 1 pago en mora = 1 mes adeudado
            #
            # Entonces:
            # Se cuentan pagos en estado mora
            # ==================================================
            if regla.incobrable_criterio == 'meses':

                cantidad_mora = self.search_count([
                    ('contract_id', '=', contract.id),
                    ('estado_pago', '=', 'mora'),
                ])

                _logger.info(
                    "Contrato %s tiene %s pagos en mora",
                    contract.name,
                    cantidad_mora
                )

                supera_incobrable = (
                    cantidad_mora >= (
                        regla.meses_incobrable or 0
                    )
                )
                _logger.info(f"supera_incobrable : {supera_incobrable} , de {regla.meses_incobrable}")

            # ==================================================
            # CRITERIO POR DÍAS
            # ==================================================
            else:

                pagos_mora = self.search([
                    ('contract_id', '=', contract.id),
                    ('estado_pago', '=', 'mora'),
                ], order='fecha_vencimiento asc', limit=1)

                if not pagos_mora:
                    continue

                pago_mas_antiguo = pagos_mora[0]

                overdue_date = self._calculate_fecha_vencimiento(
                    pago_mas_antiguo.mes,
                    pago_mas_antiguo.anio,
                    regla
                )

                if not overdue_date:
                    continue

                dias_atraso = max(
                    (today - overdue_date).days,
                    0
                )

                _logger.info(
                    "Contrato %s tiene %s días de atraso",
                    contract.name,
                    dias_atraso
                )

                supera_incobrable = (
                    dias_atraso >= (
                        regla.dias_incobrable or 0
                    )
                )

            # ==================================================
            # MARCAR CONTRATO PARA INCORBRABLE
            # ==================================================
            if supera_incobrable:

                contracts_to_check.add(contract.id)
                #_logger.info(f"contracts incobrables {contracts_to_check}")
 
        # ==================================================
        # CREAR INCORBRABLES
        # ==================================================
        for contract_id in contracts_to_check:

            contract = self.env[
                'customer.contract'
            ].browse(contract_id)
            #_logger.info(f"contracts incobrables {contract}")
            self._check_create_incobrable_from_contract(
                contract
            )

        _logger.info(
            "Total contratos enviados a incobrables: %s",
            len(contracts_to_check)
        )

        return len(contracts_to_check)
        """ for rec in pagos:
            regla = self._get_regla_for_contract(rec.contract_id)
            #_logger.info(f"la aplicada para este pago es {regla.read()}")
            if not regla:
                continue

            overdue_date = self._calculate_fecha_vencimiento(rec.mes, rec.anio, regla)
            if not overdue_date:
                continue

            dias_atraso = max((today - overdue_date).days, 0)
            _logger.info(f"Pago {rec.id} tiene {dias_atraso} días de atraso")
            meses_atraso = self._months_between_dates(overdue_date, today)
            _logger.info(f"Pago {rec.id} tiene {meses_atraso} meses de atraso")
            

            if regla.incobrable_criterio == 'meses':
                if meses_atraso >= (regla.meses_incobrable or 0):
                    contracts_to_check.add(rec.contract_id.id)
            else:
                if dias_atraso >= (regla.dias_incobrable or 0):
                    contracts_to_check.add(rec.contract_id.id)

        for contract_id in contracts_to_check:
            contract = self.env['customer.contract'].browse(contract_id)
            self._check_create_incobrable_from_contract(contract)

        return len(contracts_to_check) """

    @api.model
    def cron_procesar_cobranza(self):
        """Cron maestro diario para cobrar, evaluar mora e incobrables."""
        _logger.warning("=== CRON COBRANZA EJECUTADO ===")
        today = date.today()
        self._deactivate_legacy_crons()
        generados = self._cron_generar_deudas_diarias(today=today)
        moras = self._cron_evaluar_mora_diaria(today=today)
        incobrables = self._cron_evaluar_incobrables_diario(today=today)
        return {
            'date': today.isoformat(),
            'generated': generados,
            'mora_updated': moras,
            'incobrables_checked': incobrables,
        }

    @api.depends('partner_id', 'periodo')
    def _compute_display_name(self):
        for rec in self:
            nombre = rec.partner_id.name or ''
            rec.display_name = f"{nombre} — {rec.periodo}" if rec.periodo else nombre

    @api.depends('anio')
    def _compute_anio_display(self):
        for rec in self:
            if rec.anio:
                rec.anio_display = f"{int(rec.anio):,}".replace(',', '.')
            else:
                rec.anio_display = False

    @api.depends('client_service_id.lead_id', 'contract_id.lead_id')
    def _compute_crm_data(self):
        for rec in self:
            lead = rec.client_service_id.lead_id or rec.contract_id.lead_id
            rec.crm_lead_id = lead
            rec.crm_zona = lead.zona if lead else False
            rec.crm_direccion = lead.direccion if lead else False
            rec.crm_ubicacion = lead.ubicacion if lead else False
            rec.crm_coordenadas = lead.coordenadas if lead else False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id:
            self.contract_id = False
            self.client_service_id = False
            return

        if not self.contract_id or self.contract_id.partner_id != self.partner_id:
            self.contract_id = self._get_preferred_contract(self.partner_id)

        if not self.contract_id:
            self.client_service_id = False
            return {
                'warning': {
                    'title': 'Contrato activo requerido',
                    'message': f"El cliente '{self.partner_id.name}' no tiene contrato activo.",
                }
            }

        if not self.client_service_id or self.client_service_id.partner_id != self.partner_id:
            self.client_service_id = self._find_client_service_for_contract(self.contract_id)

        self._apply_next_period_for_new_record()

        self._sync_payment_defaults()
        self._apply_default_amounts_onchange()

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            return
        self.partner_id = self.contract_id.partner_id
        self.client_service_id = self._find_client_service_for_contract(self.contract_id) or False

        self._apply_next_period_for_new_record()

        self._sync_payment_defaults()
        self._apply_default_amounts_onchange()

    @api.onchange('monto_a_cobrar')
    def _onchange_monto_a_cobrar(self):
        # Mantener el monto pagado si el usuario ya lo ha llenado manualmente.
        # El valor por defecto se ajusta en el tipo de ajuste por defecto.
        return

    @api.onchange('client_service_id')
    def _onchange_client_service_id(self):
        if not self.client_service_id:
            return
        self.partner_id = self.client_service_id.partner_id
        if not self.contract_id or self.contract_id.partner_id != self.partner_id:
            self.contract_id = self._find_contract_for_service(self.client_service_id)

        self._apply_next_period_for_new_record()

        self._sync_payment_defaults()
        self._apply_default_amounts_onchange()

    def _get_preferred_contract(self, partner):
        Contract = self.env['customer.contract']
        contracts = Contract.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active'),
        ], order='contract_date desc, id desc')
        if not contracts:
            return False
        return contracts[0]

    def _find_client_service_for_contract(self, contract):
        if not contract:
            return False
        ClientService = self.env['wigo.ftth.client.service']

        if contract.lead_id:
            svc = ClientService.search([('lead_id', '=', contract.lead_id.id)], limit=1)
            if svc:
                return svc

        if contract.name:
            svc = ClientService.search([('codigo_cliente', '=', contract.name)], limit=1)
            if svc:
                return svc

        svc = ClientService.search([
            ('partner_id', '=', contract.partner_id.id),
            ('plan_id', '=', contract.plan_id.id),
        ], limit=1)
        return svc or ClientService.search([('partner_id', '=', contract.partner_id.id)], limit=1)

    def _find_contract_for_service(self, service):
        if not service:
            return False
        Contract = self.env['customer.contract']

        domain_base = [
            ('partner_id', '=', service.partner_id.id),
            ('state', '=', 'active'),
        ]

        if service.lead_id:
            contract = Contract.search(domain_base + [('lead_id', '=', service.lead_id.id)], limit=1)
            if contract:
                return contract

        contract = Contract.search(domain_base + [('name', '=', service.codigo_cliente)], limit=1)
        if contract:
            return contract

        if service.plan_id:
            contract = Contract.search(domain_base + [('plan_id', '=', service.plan_id.id)], limit=1)
            if contract:
                return contract

        return Contract.search(domain_base, order='contract_date desc, id desc', limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        Contract = self.env['customer.contract']
        ClientService = self.env['wigo.ftth.client.service']
        seen_period_keys = set()
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            contract_id = vals.get('contract_id')
            service_id = vals.get('client_service_id')

            if partner_id and not contract_id:
                partner = self.env['res.partner'].browse(partner_id)
                contract = self._get_preferred_contract(partner)
                if contract:
                    vals['contract_id'] = contract.id
                    contract_id = contract.id
                else:
                    raise ValidationError(
                        f"El cliente '{partner.name}' no tiene contrato activo."
                    )

            if contract_id and not service_id:
                contract = Contract.browse(contract_id)
                service = self._find_client_service_for_contract(contract)
                if service:
                    vals['client_service_id'] = service.id
                    service_id = service.id

            if service_id and not partner_id:
                service = ClientService.browse(service_id)
                vals['partner_id'] = service.partner_id.id

            if not vals.get('mes') or not vals.get('anio'):
                mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                    contract=Contract.browse(contract_id) if contract_id else None,
                    client_service=ClientService.browse(service_id) if service_id else None,
                    partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
                )
                vals.setdefault('mes', mes_sugerido)
                vals.setdefault('anio', anio_sugerido)

            if not vals.get('fecha_pago'):
                vals['fecha_pago'] = fields.Date.context_today(self)

            tipo_ajuste_id = vals.get('tipo_ajuste_id')
            tipo_ajuste = self.env['wigo.cobranza.tipo_ajuste'].browse(tipo_ajuste_id) if tipo_ajuste_id else False
            if not tipo_ajuste and vals.get('es_primer_mes'):
                tipo_ajuste = self._get_legacy_proration_tipo_ajuste()
                if tipo_ajuste:
                    vals['tipo_ajuste_id'] = tipo_ajuste.id
            if not tipo_ajuste:
                tipo_ajuste = self._get_default_tipo_ajuste()
                if tipo_ajuste and not vals.get('tipo_ajuste_id'):
                    vals['tipo_ajuste_id'] = tipo_ajuste.id

            if tipo_ajuste:
                vals['es_primer_mes'] = bool(tipo_ajuste.enable_proration)
                if not tipo_ajuste.enable_proration:
                    vals['monto_prorrateo'] = 0.0
                else:
                    vals.setdefault('monto_prorrateo', 0.0)
                if not tipo_ajuste.requires_reason:
                    vals['motivo'] = False
                if tipo_ajuste.is_default:
                    vals['monto_a_cobrar_manual'] = 0.0
                    vals['monto_a_cobrar_manual_aplicado'] = False
            else:
                vals.setdefault('monto_prorrateo', 0.0)
                vals.setdefault('motivo', False)

            if not vals.get('mes') or not vals.get('anio'):
                mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                    contract=Contract.browse(contract_id) if contract_id else None,
                    client_service=ClientService.browse(service_id) if service_id else None,
                    partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
                )
                vals['mes'] = mes_sugerido
                vals['anio'] = anio_sugerido

            period_key = (
                contract_id or service_id or partner_id,
                str(vals.get('mes')),
                int(vals.get('anio') or 0),
            )
            if period_key in seen_period_keys:
                raise ValidationError(
                    'Ya existe un cobro para el mismo período dentro de la misma operación de creación.'
                )
            seen_period_keys.add(period_key)

            duplicate = self._get_existing_payment_for_period(
                contract=Contract.browse(contract_id) if contract_id else None,
                client_service=ClientService.browse(service_id) if service_id else None,
                partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
                mes=vals['mes'],
                anio=vals['anio'],
            )
            if duplicate:
                raise ValidationError(
                    f"Ya existe un registro de cobro para el período {vals['mes']}/{vals['anio']} "
                    f"en el cliente o contrato seleccionado."
                )

            # Poblar modalidad de pago desde el contrato (no editable manualmente)
            if vals.get('contract_id'):
                contract = Contract.browse(vals.get('contract_id'))
                vals['payment_mode'] = contract.payment_mode if contract and contract.payment_mode else False

            # Establecer estado inicial UNIFORME en 'pendiente'.
            # Reglas de mora deben evaluarse posteriormente por el cron
            # o por procesos que centralicen la lógica de mora.
            vals['estado_pago'] = 'pendiente'

        records = super().create(vals_list)
        # Sincronizar valores por defecto para registros persistidos
        records._sync_payment_defaults()

        # Si el tipo de ajuste es la opción por defecto, fijar monto_pagado = monto_a_cobrar
        # y evitar re-trigger de _sync_payment_defaults usando contexto
        defaults = records.filtered(lambda r: r.tipo_ajuste_id and r.tipo_ajuste_id.is_default)
        if defaults:
            for rec in defaults:
                # escribir con contexto para evitar sincronizar otra vez
                rec.with_context(skip_sync_payment_defaults=True).write({'monto_pagado': rec.monto_a_cobrar or 0.0})

        # NOTA: No aplicar ninguna evaluación de mora en create().
        # La evaluación de mora debe ejecutarse exclusivamente desde el cron
        # (cron_procesar_cobranza / _cron_evaluar_mora_diaria) o funciones explícitas.
        return records

    def write(self, vals):
        contable_fields = {'monto_a_cobrar', 'monto_pagado'}
        contable_changed = any(field in vals for field in contable_fields)
        audit_payload = []

        if contable_changed:
            justificacion = (vals.get('justificacion_edicion') or '').strip()
            for rec in self:
                # Permitir edición en pendiente/mora. Bloquear sin justificación
                # solo cuando el pago ya está confirmado (al_dia/pagado).
                if rec.estado_pago in ('pagado', 'al_dia') and not justificacion:
                    raise ValidationError(
                        'Debe indicar una justificación para editar valores contables cuando el pago ya fue confirmado (al día/pagado).'
                    )
                audit_payload.append({
                    'id': rec.id,
                    'old': {
                        'monto_a_cobrar': rec.monto_a_cobrar,
                        'monto_pagado': rec.monto_pagado,
                    },
                    'justificacion': justificacion,
                    'usuario': self.env.user.display_name,
                    'fecha': fields.Datetime.now(),
                })

        if 'tipo_ajuste_id' in vals:
            tipo_ajuste = self.env['wigo.cobranza.tipo_ajuste'].browse(vals.get('tipo_ajuste_id')) if vals.get('tipo_ajuste_id') else False
            if tipo_ajuste:
                vals['es_primer_mes'] = bool(tipo_ajuste.enable_proration)
                if not tipo_ajuste.enable_proration:
                    vals['monto_prorrateo'] = 0.0
                else:
                    vals.setdefault('monto_prorrateo', 0.0)
                if not tipo_ajuste.requires_reason:
                    vals['motivo'] = False
                if tipo_ajuste.is_default:
                    vals['monto_a_cobrar_manual'] = 0.0
                    vals['monto_a_cobrar_manual_aplicado'] = False
            else:
                vals['es_primer_mes'] = False
                vals['monto_prorrateo'] = 0.0
                vals['motivo'] = False
        elif 'es_primer_mes' in vals:
            if vals.get('es_primer_mes'):
                tipo_ajuste = self._get_legacy_proration_tipo_ajuste()
                if tipo_ajuste:
                    vals['tipo_ajuste_id'] = tipo_ajuste.id
                    vals['es_primer_mes'] = bool(tipo_ajuste.enable_proration)
                    if not tipo_ajuste.enable_proration:
                        vals['monto_prorrateo'] = 0.0
                    else:
                        vals.setdefault('monto_prorrateo', 0.0)
                    if not tipo_ajuste.requires_reason:
                        vals['motivo'] = False
            else:
                vals['monto_prorrateo'] = 0.0
                vals['motivo'] = False

        res = super().write(vals)

        if contable_changed:
            for rec in self:
                payload = next((item for item in audit_payload if item['id'] == rec.id), None)
                if not payload:
                    continue
                nuevos = {
                    'monto_a_cobrar': rec.monto_a_cobrar,
                    'monto_pagado': rec.monto_pagado,
                }
                if payload['old'] != nuevos:
                    rec.message_post(
                        body=(
                            f"<b>Edición contable registrada</b><br/>"
                            f"Usuario: {payload['usuario']}<br/>"
                            f"Fecha: {payload['fecha']}<br/>"
                            f"Monto a cobrar anterior: {payload['old']['monto_a_cobrar']:.2f} → nuevo: {nuevos['monto_a_cobrar']:.2f}<br/>"
                            f"Monto pagado anterior: {payload['old']['monto_pagado']:.2f} → nuevo: {nuevos['monto_pagado']:.2f}<br/>"
                            f"Justificación: {payload['justificacion'] or 'Sin justificación'}"
                        ),
                        subtype_xmlid='mail.mt_note',
                    )

        # Only trigger sync when not explicitly skipped via context
        if not self.env.context.get('skip_sync_payment_defaults') and any(k in vals for k in ('tipo_ajuste_id', 'es_primer_mes', 'monto_prorrateo', 'monto_plan', 'motivo')):
            self._sync_payment_defaults()
        return res

    def action_editar_valores_contables(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar valores contables',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': dict(self.env.context, contabilidad_editable=True, form_view_initial_mode='edit'),
        }

    def action_open_contract_crm(self):
        self.ensure_one()
        lead = self._get_won_lead_for_contract()
        if not lead:
            raise UserError(
                'No se encontró un lead ganado de CRM para este contrato/cliente.'
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM - Cliente Ganado',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': lead.id,
            'target': 'current',
        }

    def _get_won_lead_for_contract(self):
        self.ensure_one()
        Lead = self.env['crm.lead']

        if self.contract_id and self.contract_id.lead_id and self.contract_id.lead_id.stage_id.is_won:
            return self.contract_id.lead_id

        domain = [('stage_id.is_won', '=', True)]
        if self.contract_id:
            domain = [('contract_id', '=', self.contract_id.id)] + domain
        elif self.partner_id:
            domain = [('partner_id', '=', self.partner_id.id)] + domain

        lead = Lead.search(domain, order='write_date desc, id desc', limit=1)
        if lead:
            return lead

        if self.partner_id:
            return Lead.search([
                ('partner_id', '=', self.partner_id.id),
                ('stage_id.is_won', '=', True),
            ], order='write_date desc, id desc', limit=1)

        return False

    # ─────────────────────────────────────────────────────────────
    # Business logic
    # ─────────────────────────────────────────────────────────────
    def action_registrar_pago(self):
        """Marcar como pagado, notificar a técnica si había suspensión pendiente."""
        for rec in self:
            if not rec.monto_pagado or not rec.fecha_pago:
                raise ValidationError(
                    'Debe ingresar el monto pagado y la fecha de pago antes de confirmar.'
                )
            nuevo_estado = 'pagado' if rec.monto_pagado >= rec.monto_a_cobrar else 'pendiente'
            rec.write({'estado_pago': nuevo_estado})
            
            # Actualizar monto_cobrado en registro incobrable si existe
            if rec.contract_id:
                Incobrable = self.env['wigo.incobrable']
                incobrables = Incobrable.search([
                    ('contract_id', '=', rec.contract_id.id),
                    ('state', 'not in', ['recuperado', 'baja_incobrable']),
                ])
                if incobrables:
                    for incobrable in incobrables:
                        incobrable.write({
                            'monto_cobrado': incobrable.monto_cobrado + rec.monto_pagado
                        })
            
            svc = rec.client_service_id
            if svc:
                if nuevo_estado == 'pagado' and svc.estado_servicio == 'suspended':
                    svc.write({'estado_servicio': 'active'})
                    svc.message_post(
                        body=(
                            f"✅ <b>Pago registrado por cobranza.</b> "
                            f"Cliente <b>{svc.codigo_cliente}</b>paid Bs. {rec.monto_pagado:.2f} "
                            f"({rec.periodo}). "
                            f"<b>Proceder con la REACTIVACIÓN del servicio en la OLT.</b>"
                        ),
                        subtype_xmlid='mail.mt_comment',
                        partner_ids=self._get_tech_partner_ids(),
                    )
        rec.message_post(
                body=f"Pago de Bs. {rec.monto_pagado:.2f} registrado vía {dict(rec._fields['canal_pago'].selection).get(rec.canal_pago, '')}."
            )
        return True

    def _recompute_contract_mora(self):
        """
        Mantenimiento auxiliar de contrato/servicio.

        Importante: esta rutina NO debe cambiar `estado_pago` a mora.
        La transición a mora queda exclusivamente a cargo del cron.
        """
        contracts = self.mapped('contract_id').filtered(lambda c: c)
        if not contracts:
            return
        from datetime import date as _date

        for contract in contracts:
            pagos = self.search([('contract_id', '=', contract.id)])
            today = _date.today()
            # Obtener regla una sola vez por contrato
            regla_contrato = self._get_regla_for_contract(contract)

            # Evaluar cada pago individualmente: calcular fecha_vencimiento
            # a partir de mes/anio y la regla (no depender del campo computed)
            for rec in pagos:
                try:
                    if rec.estado_pago == 'pagado':
                        continue

                    # Calcular fecha de vencimiento aplicada por la regla
                    fecha_venc = False
                    if regla_contrato:
                        fecha_venc = self._calculate_fecha_vencimiento(rec.mes, rec.anio, regla_contrato)
                    else:
                        # fallback al campo si no hay regla
                        fecha_venc = rec.fecha_vencimiento

                    if not fecha_venc:
                        continue

                    # Marcar en mora si hoy es la fecha de vencimiento o posterior
                    # No mutar estado_pago aquí. Solo usar la información para
                    # mantenimiento posterior (servicio, incobrables, etc.).
                    if today < fecha_venc:
                        continue
                except Exception:
                    continue

            # Mantener la acción de suspensión / creación de incobrables basada
            # en la cantidad de impagos, pero sin marcar masivamente registros.
            unpaid = pagos.filtered(lambda p: p.estado_pago in ('pendiente', 'mora'))
            if len(unpaid) >= 3:
                latest = unpaid.sorted(
                    key=lambda r: (r.anio or 0, int(r.mes or 0), r.id),
                    reverse=True,
                )[:1]
                latest_rec = latest and latest[0] or False
                service = latest_rec.client_service_id if latest_rec else self._find_client_service_for_contract(contract)
                if service:
                    vals = {}
                    if 'estado_servicio' in service._fields and service.estado_servicio != 'baja':
                        vals['estado_servicio'] = 'suspended'
                    if vals:
                        service.write(vals)

                # Usar regla para decidir si crear incobrable
                regla = self._get_regla_for_contract(contract)
                if regla:
                    self._check_create_incobrable_from_contract(contract)

    def _check_create_incobrable_from_contract(self, contract):
        """
        Crea o actualiza automáticamente un registro incobrable
        para un contrato que tiene pagos en mora.
        """

        if not contract:
            return

        regla = self._get_regla_for_contract(contract)

        if not regla:
            return

        # =========================================================
        # MODELO INCORBRABLE
        # =========================================================
        Incobrable = self.env['wigo.incobrable'].sudo()

        # =========================================================
        # OBTENER PAGOS EN MORA
        # =========================================================
        pagos_mora = self.search([
            ('contract_id', '=', contract.id),
            ('estado_pago', '=', 'mora'),
        ], order='anio asc, mes asc')
        
        if not pagos_mora:
            return

        # =========================================================
        # CALCULAR DATOS
        # =========================================================
        cantidad_periodos = len(pagos_mora)

        monto_total = sum(
            pagos_mora.mapped('monto_a_cobrar')
        )

        periodos = ', '.join(
            pagos_mora.mapped('periodo')
        )

        svc = self._find_client_service_for_contract(
            contract
        )

        # =========================================================
        # BUSCAR INCORBRABLE ACTIVO EXISTENTE
        # =========================================================
        ya_existe = Incobrable.search([
            ('partner_id', '=', contract.partner_id.id),
            ('contract_id', '=', contract.id),
            ('state', 'not in', ['recuperado']),
        ], limit=1)

        # =========================================================
        # ACTUALIZAR INCORBRABLE EXISTENTE
        # =========================================================
        if ya_existe:

            ya_existe.write({
                'meses_adeudados': periodos,
                'monto_total_adeudado': monto_total,
                'observaciones': (
                    f'Actualizado automáticamente: '
                    f'{cantidad_periodos} períodos en mora. '
                    f'Modalidad: {regla.name}.'
                ),
            })

            _logger.info(
                "Incobrable actualizado para contrato %s",
                contract.name
            )

            return ya_existe

        # =========================================================
        # CREAR NUEVO INCORBRABLE
        # =========================================================
        incobrable = Incobrable.create({
            'partner_id': contract.partner_id.id,
            'contract_id': contract.id,
            'client_service_id': svc.id if svc else False,
            'meses_adeudados': periodos,
            'monto_total_adeudado': monto_total,
            'state': 'activo',
            'observaciones': (
                f'Generado automáticamente: '
                f'{cantidad_periodos} períodos en mora. '
                f'Modalidad: {regla.name}.'
            ),
        })

        _logger.info(
            "Incobrable creado para contrato %s",
            contract.name
        )

        # =========================================================
        # MENSAJE EN CHATTER DEL SERVICIO
        # =========================================================
        if svc:

            svc.message_post(
                body=(
                    f"⚠️ <b>Cliente trasladado a incobrables automáticamente.</b> "
                    f"Código: <b>{svc.codigo_cliente}</b> — "
                    f"{svc.partner_id.name}. "
                    f"Períodos en mora: <b>{periodos}</b>."
                ),
                subtype_xmlid='mail.mt_comment',
                partner_ids=self._get_tech_partner_ids(),
            )

        # =========================================================
        # NOTIFICACIÓN A COBRANZA
        # =========================================================
        cobranza_group = self.env.ref(
            'wigo_cobranza.group_cobranza',
            raise_if_not_found=False
        )

        if cobranza_group:

            partners = cobranza_group.user_ids.mapped(
                'partner_id'
            )

            if partners:

                self.env['mail.message'].sudo().create({
                    'message_type': 'notification',
                    'body': (
                        f"🚨 <b>{contract.partner_id.name}</b> "
                        f"trasladado a incobrables "
                        f"por {cantidad_periodos} períodos en mora."
                    ),
                    'partner_ids': partners.ids,
                    'model': 'wigo.incobrable',
                    'res_id': incobrable.id,
                })

        return incobrable

    def action_marcar_mora(self):
        """Acción manual deshabilitada para cambios de estado.

        La transición a `mora` queda exclusivamente en manos del cron.
        """
        for rec in self:
            svc = rec.client_service_id
            if svc:
                svc.message_post(
                    body=(
                        f"Se solicitó revisión de mora para el período {rec.periodo}. "
                        f"La actualización de estado se ejecuta únicamente por el cron automático."
                    ),
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=self._get_tech_partner_ids(),
                )

    def action_instruir_baja(self):
        """Instruir baja definitiva al área técnica."""
        for rec in self:
            rec.estado_pago = 'baja_definitiva'
            svc = rec.client_service_id
            if svc:
                svc.estado_pago = 'baja_definitiva'
                svc.estado_servicio = 'baja'
                svc.fecha_baja = date.today()
                svc.message_post(
                    body=(
                        f"⛔ BAJA DEFINITIVA instruida por Contabilidad."
                        f"Cliente: {svc.codigo_cliente} — {svc.partner_id.name}. "
                        f"<b>Área Técnica: retirar equipo ONU y actualizar estado en sistema.</b>"
                    ),
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=self._get_tech_partner_ids(),
                )

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def _get_tech_partner_ids(self):
        """Retorna los partner_ids de usuarios del grupo técnico FTTH."""
        group = self.env.ref('wigo_ftth.group_ftth_tech', raise_if_not_found=False)
        if not group:
            return []
        return group.user_ids.mapped('partner_id').ids

    def _get_all_comprobante_attachments(self):
        self.ensure_one()
        return self.comprobante_attachment_ids

    def _get_comprobante_url(self, download=False):
        self.ensure_one()
        attachments = self._get_all_comprobante_attachments()
        if attachments:
            att = attachments[0]
            suffix = '?download=true' if download else ''
            return f'/web/content/{att.id}{suffix}'

        if not self.comprobante_adjunto:
            return False

        return (
            f"/web/content?model=wigo.pago.estado&id={self.id}"
            f"&field=comprobante_adjunto&filename_field=comprobante_adjunto_fname"
            f"&download={'true' if download else 'false'}"
        )

    def action_ver_comprobante(self):
        self.ensure_one()
        if len(self._get_all_comprobante_attachments()) > 1:
            return self._open_attachment_selector_wizard(action_type='view')
        
        url = self._get_comprobante_url(download=False)
        if not url:
            raise UserError('No hay comprobante adjunto para mostrar.')
            
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_descargar_comprobante(self):
        self.ensure_one()
        if len(self._get_all_comprobante_attachments()) > 1:
            return self._open_attachment_selector_wizard(action_type='download')
            
        url = self._get_comprobante_url(download=True)
        if not url:
            raise UserError('No hay comprobante adjunto para descargar.')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    def _open_attachment_selector_wizard(self, action_type='view'):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar comprobante',
            'res_model': 'wigo.pago.estado.attachment.viewer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pago_id': self.id,
                'default_action_type': action_type,
            },
        }


    # ─────────────────────────────────────────────────────────────
    # Recibo de cobro
    # ─────────────────────────────────────────────────────────────
    # recibo_id: stored + compute para que el frontend siempre lo tenga disponible
    recibo_id = fields.Many2one(
        'wigo.recibo.cobro',
        string='Recibo de cobro',
        compute='_compute_recibo_id',
        compute_sudo=True,
        copy=False,
    )
    
    # recibo_generado: computed field que sincroniza automáticamente con recibo_id
    recibo_generado = fields.Boolean(
        string='Recibo generado',
        compute='_compute_recibo_generado',
        copy=False,
    )

    @api.depends()
    def _compute_recibo_id(self):
        """Busca SIEMPRE recibos válidos (NO anulados) asociados al pago. Sin cache."""
        Recibo = self.env['wigo.recibo.cobro']
        for rec in self:
            # Búsqueda fresh cada vez, SIN cache
            recibo = Recibo.sudo().search(
                [('pago_id', '=', rec.id), ('state', '!=', 'anulado')],
                limit=1,
                order='id DESC'
            )
            rec.recibo_id = recibo.id if recibo else False

    @api.depends('recibo_id')
    def _compute_recibo_generado(self):
        """Sincroniza automáticamente: si existe recibo_id, entonces recibo_generado = True."""
        for rec in self:
            rec.recibo_generado = bool(rec.recibo_id)

    def _get_or_create_recibo(self):
        """Obtiene el recibo existente NO ANULADO o crea uno nuevo."""
        self.ensure_one()
        Recibo = self.env['wigo.recibo.cobro']
        # Busca recibos VÁLIDOS (NO anulados) asociados al pago
        recibo = Recibo.search(
            [('pago_id', '=', self.id), ('state', '!=', 'anulado')],
            limit=1,
            order='id DESC'  # Más reciente primero
        )
        if not recibo:
            # Si no existe ninguno válido (ej: RC-0001 anulado), crea uno nuevo con nuevo número
            recibo = Recibo.create({'pago_id': self.id})
            # recibo_generado se actualiza automáticamente via _compute_recibo_generado
        return recibo

    def action_generar_recibo(self):
        """Crea el recibo y abre el formulario para editarlo."""
        self.ensure_one()
        if self.estado_pago not in ('pagado', 'pendiente'):
            raise UserError(
                'Solo se puede generar recibo para pagos confirmados (Pagado o Pendiente).'
            )
        recibo = self._get_or_create_recibo()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Recibo — {self.display_name}',
            'res_model': 'wigo.recibo.cobro',
            'view_mode': 'form',
            'res_id': recibo.id,
            'target': 'current',
        }

    def action_abrir_recibo(self):
        """Abre el form del recibo existente NO ANULADO (editar / imprimir)."""
        self.ensure_one()
        # Busca solo recibos VÁLIDOS (NO anulados)
        recibo = self.env['wigo.recibo.cobro'].search(
            [('pago_id', '=', self.id), ('state', '!=', 'anulado')],
            limit=1,
            order='id DESC'
        )
        if not recibo:
            return self.action_generar_recibo()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Recibo — {self.display_name}',
            'res_model': 'wigo.recibo.cobro',
            'view_mode': 'form',
            'res_id': recibo.id,
            'target': 'current',
        }

    def action_imprimir_recibo(self):
        """Imprime el recibo PDF directamente (crea si no existe)."""
        self.ensure_one()
        recibo = self._get_or_create_recibo()
        return recibo.action_imprimir()

    # ─────────────────────────────────────────────────────────────
    # Facturación
    # ─────────────────────────────────────────────────────────────
    def action_registrar_factura(self):
        """Abre un formulario para registrar la factura vinculada a este pago."""
        self.ensure_one()
        Factura = self.env['wigo.factura.cobranza']
        factura = Factura.search([('pago_id', '=', self.id), ('state', '!=', 'anulada')], limit=1)
        ctx = {
            'default_pago_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_contract_id': self.contract_id.id if self.contract_id else False,
            'default_monto_total': self.monto_pagado,
            'default_periodo_facturado': self.periodo,
            'default_fecha_emision': str(self.fecha_pago or fields.Date.context_today(self)),
        }
        return {
            'type': 'ir.actions.act_window',
            'name': f'Factura — {self.display_name}',
            'res_model': 'wigo.factura.cobranza',
            'view_mode': 'form',
            'views': [(self.env.ref('wigo_cobranza.view_invoice_form_emit').id, 'form')],
            'res_id': factura.id if factura else False,
            'target': 'new',
            'context': ctx,
        }

    # ─────────────────────────────────────────────────────────────
    # Navegación desde planilla al cliente
    # ─────────────────────────────────────────────────────────────
    def action_open_partner(self):
        """Navega a la ficha del cliente desde la planilla."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.partner_id.name,
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
        }

    # ─────────────────────────────────────────────────────────────
    # Cron actions
    # ─────────────────────────────────────────────────────────────
    @api.model
    def cron_alertar_mora_dia1(self):
        return self.cron_procesar_cobranza()

    @api.model
    def action_open_registros_cobro(self):
        self._ensure_current_month_records()
        return self.env.ref('wigo_cobranza.action_payment_state').read()[0]

    @api.model
    def _ensure_current_month_records(self):
        return self._cron_generar_deudas_diarias(today=date.today())

    @api.model
    def cron_evaluar_cobranza(self):
        return self.cron_procesar_cobranza()

    def _notify_mora(self, rec, regla):
        """Notifica a cobranza sobre cliente en mora."""
        cobranza_group = self.env.ref('wigo_cobranza.group_cobranza', raise_if_not_found=False)
        if cobranza_group:
            partners = cobranza_group.user_ids.mapped('partner_id')
            if partners:
                self.env['mail.message'].create({
                    'message_type': 'notification',
                    'body': (
                        f"Cliente {rec.partner_id.name} en mora. "
                        f"Días de atraso: {rec.dias_atraso}. "
                        f"Regla: {regla.name}."
                    ),
                    'partner_ids': partners.ids,
                    'model': 'wigo.pago.estado',
                    'res_id': rec.id,
                })

    @api.model
    def cron_detectar_incobrables(self):
        return self.cron_procesar_cobranza()

    @api.model
    def cron_alertar_suspension(self):
        return self.cron_procesar_cobranza()


class WigoPagoEstadoAttachmentViewerWizard(models.TransientModel):
    _name = 'wigo.pago.estado.attachment.viewer.wizard'
    _description = 'Seleccionar adjunto de pago'

    pago_id = fields.Many2one(
        'wigo.pago.estado',
        string='Registro de Pago',
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

    @api.depends('pago_id')
    def _compute_available_attachment_ids(self):
        for rec in self:
            rec.available_attachment_ids = rec.pago_id._get_all_comprobante_attachments()
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
