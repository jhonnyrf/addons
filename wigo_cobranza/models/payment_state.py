import base64
from datetime import date, datetime
from calendar import monthrange
from html import escape
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class WigoPagoEstado(models.Model):
    _name = 'wigo.pago.estado'
    _description = 'Registro estatal de pago'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anio desc, mes desc, partner_id'
    _rec_name = 'display_name'

    # ── Partner / Contract / Service ──────────────────────────
    eligible_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_eligible_partner_ids',
        string='Clientes con contrato activo', store=False,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict', tracking=True, index=True,
        domain="[('id', 'in', eligible_partner_ids)]",
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
        domain="[('partner_id', '=', partner_id), ('state', '=', 'active')]",
        tracking=True, required=True,
    )
    client_service_id = fields.Many2one(
        'wigo.ftth.client.service', string='Servicio (CF)',
        domain="[('partner_id', '=', partner_id)]",
        ondelete='restrict', tracking=True, index=True,
    )
    codigo_cliente = fields.Char(
        string='Código CF', compute='_compute_contract_service_data', store=True, readonly=True,
    )
    plan_id = fields.Many2one(
        'internet.plan', string='Plan',
        compute='_compute_contract_service_data', store=True, readonly=True,
    )
    partner_ci = fields.Char(
        string='CI', compute='_compute_partner_snapshot', store=False,
    )
    partner_celular = fields.Char(
        string='Celular', compute='_compute_partner_snapshot', store=False,
    )
    partner_telefono = fields.Char(
        string='Teléfono', compute='_compute_partner_snapshot', store=False,
    )
    partner_email = fields.Char(
        string='Correo', compute='_compute_partner_snapshot', store=False,
    )
    partner_direccion = fields.Char(
        string='Dirección', compute='_compute_partner_snapshot', store=False,
    )
    contract_state = fields.Selection(
        related='contract_id.state', string='Estado de contrato',
        readonly=True, store=False,
    )
    crm_lead_id = fields.Many2one(
        'crm.lead', string='Lead CRM',
        compute='_compute_crm_data', store=False, readonly=True,
    )
    crm_zona = fields.Char(
        string='Zona CRM', compute='_compute_crm_data', store=False,
    )
    crm_direccion = fields.Char(
        string='Dirección CRM', compute='_compute_crm_data', store=False,
    )
    crm_ubicacion = fields.Char(
        string='Ubicación CRM', compute='_compute_crm_data', store=False,
    )
    crm_coordenadas = fields.Char(
        string='Coordenadas CRM', compute='_compute_crm_data', store=False,
    )

    # ── Period ────────────────────────────────────────────────
    anio = fields.Char(string='Año', required=True)
   
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

    # ── Amounts ───────────────────────────────────────────────
    monto_plan = fields.Float(
        string='Monto del plan (Bs)',
        related='plan_id.price', store=True, readonly=True,
    )
    payment_mode = fields.Selection(
        [('prepaid', 'Prepago'), ('postpaid', 'Postpago')],
        string='Modalidad de pago',
        compute='_compute_payment_mode', store=True, readonly=True,
    )
    monto_prorrateo = fields.Float(
        string='Monto prorrateo (Bs)', default=0.0,
    )
    tipo_ajuste_id = fields.Many2one(
        'wigo.cobranza.tipo_ajuste', string='Tipo de ajuste',
        ondelete='restrict', tracking=True,
    )
    tipo_ajuste_is_default = fields.Boolean(
        related='tipo_ajuste_id.is_default', string='Tipo de ajuste por defecto',
        readonly=True, store=False,
    )
    tipo_ajuste_enable_proration = fields.Boolean(
        related='tipo_ajuste_id.enable_proration', string='Tipo habilita prorrateo',
        readonly=True, store=False,
    )
    tipo_ajuste_requires_reason = fields.Boolean(
        related='tipo_ajuste_id.requires_reason', string='Tipo requiere motivo',
        readonly=True, store=False,
    )
    tipo_ajuste_color = fields.Integer(
        related='tipo_ajuste_id.color', string='Color de tipo de ajuste',
        readonly=True, store=False,
    )
    es_primer_mes = fields.Boolean(
        string='¿Es primer mes?', default=False,
    )
    motivo = fields.Text(string='Motivo')
    monto_a_cobrar = fields.Float(
        string='Monto a cobrar (Bs)',
        compute='_compute_monto_a_cobrar', store=True,
        inverse='_inverse_monto_a_cobrar',
    )
    monto_a_cobrar_manual = fields.Float(
        string='Monto a cobrar manual (Bs)',
        default=False, copy=False,
    )
    monto_a_cobrar_manual_aplicado = fields.Boolean(
        string='Override de monto a cobrar aplicado',
        default=False, copy=False,
    )
    generado_automaticamente = fields.Boolean(
        string='Generado automáticamente',
        default=False, copy=False, tracking=True,
    )
    monto_pagado = fields.Float(
        string='Monto pagado (Bs)', tracking=True,
    )
    diferencia = fields.Float(
        string='Diferencia (Bs)',
        compute='_compute_diferencia', store=True,
    )

    # ── Payment Info ──────────────────────────────────────────
    fecha_pago = fields.Date(
        string='Fecha de pago', tracking=True,
        default=lambda self: fields.Date.context_today(self),
    )
    canal_pago = fields.Selection([
        ('qr', 'QR bancario'),
        ('transferencia', 'Transferencia bancaria'),
        ('efectivo', 'Efectivo en oficina'),
    ], string='Canal de pago', tracking=True)
    comprobante = fields.Char(string='Referencia / N° comprobante', tracking=True)
    comprobante_adjunto = fields.Binary(string='Comprobante (imagen o PDF)')
    comprobante_adjunto_fname = fields.Char()
    comprobante_attachment_ids = fields.Many2many(
        'ir.attachment',
        'wigo_pago_estado_attachment_rel',
        'pago_id', 'attachment_id',
        string='Comprobantes adjuntos', copy=False,
    )
    comprobante_adjunto_is_image = fields.Boolean(
        string='Adjunto es imagen',
        compute='_compute_comprobante_adjunto_type', store=False,
    )
    comprobante_adjunto_is_pdf = fields.Boolean(
        string='Adjunto es PDF',
        compute='_compute_comprobante_adjunto_type', store=False,
    )
    has_comprobante = fields.Boolean(
        string='Tiene comprobante',
        compute='_compute_has_comprobante', store=False,
    )
    registrado_por = fields.Many2one(
        'res.users', string='Registrado por',
        default=lambda self: self.env.user, tracking=True,
    )
    contabilidad_editable = fields.Boolean(
        string='Modo edición contable',
        compute='_compute_contabilidad_editable', store=False,
    )

    # ── Payment State ─────────────────────────────────────────
    estado_pago = fields.Selection([
    ('pagado', 'Pagado'),
    ('mora', 'Mora'),
    ('pendiente', 'Pendiente'),
    ], string='Estado de pago', default='pendiente',
       required=True, tracking=True, index=True,
    )
    fecha_vencimiento = fields.Date(
        string='Fecha de vencimiento',
        compute='_compute_fecha_vencimiento', store=True,
    )
    dias_atraso = fields.Integer(
        string='Días de atraso',
        compute='_compute_dias_atraso', store=False,
    )
    puede_marcar_mora_manual = fields.Boolean(
        string='Puede marcar mora manualmente',
        compute='_compute_puede_marcar_mora_manual', store=False,
    )

    notas = fields.Text(string='Notas de cobranza')
    justificacion_edicion = fields.Text(string='Justificación de edición contable')

    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── Receipt ───────────────────────────────────────────────
    recibo_id = fields.Many2one(
        'wigo.recibo.cobro', string='Recibo de cobro',
        compute='_compute_recibo_id', compute_sudo=True, copy=False,
    )
    recibo_generado = fields.Boolean(
        string='Recibo generado',
        compute='_compute_recibo_generado', copy=False,
    )

    # ═══════════════════════════════════════════════════════════
    # Computed Fields
    # ═══════════════════════════════════════════════════════════

    @api.depends('comprobante_adjunto', 'comprobante_attachment_ids')
    def _compute_has_comprobante(self):
        for rec in self:
            rec.has_comprobante = bool(rec.comprobante_adjunto or rec.comprobante_attachment_ids)

    @api.depends_context('contabilidad_editable')
    def _compute_contabilidad_editable(self):
        editable = bool(self.env.context.get('contabilidad_editable'))
        for rec in self:
            rec.contabilidad_editable = editable

    @api.depends('anio', 'mes')
    def _compute_periodo(self):
        for rec in self:
            if rec.mes and rec.anio:
                month_name = dict(self._fields['mes'].selection).get(rec.mes, '')
                rec.periodo = f"{month_name} {rec.anio}".strip()
            else:
                rec.periodo = ''

    def _compute_eligible_partner_ids(self):
        partner_ids = self.env['customer.contract'].search([
            ('state', '=', 'active'),
        ]).mapped('partner_id').ids
        for rec in self:
            rec.eligible_partner_ids = [(6, 0, partner_ids)]

    @api.depends('contract_id.name', 'contract_id.plan_id',
                 'client_service_id.codigo_cliente', 'client_service_id.plan_id')
    def _compute_contract_service_data(self):
        for rec in self:
            rec.codigo_cliente = (
                rec.contract_id.name or rec.client_service_id.codigo_cliente or False
            )
            rec.plan_id = (
                rec.contract_id.plan_id or rec.client_service_id.plan_id or False
            )

    @api.depends('contract_id.payment_mode')
    def _compute_payment_mode(self):
        for rec in self:
            rec.payment_mode = rec.contract_id.payment_mode if rec.contract_id else False

    @api.depends('partner_id')
    def _compute_partner_snapshot(self):
        for rec in self:
            partner = rec.partner_id
            if partner:
                rec.partner_ci = getattr(partner, 'ci', False) or False
                rec.partner_celular = (
                    getattr(partner, 'celular', False)
                    or getattr(partner, 'mobile', False)
                    or getattr(partner, 'phone', False)
                    or False
                )
                rec.partner_telefono = getattr(partner, 'phone', False) or False
                rec.partner_email = partner.email or False
                rec.partner_direccion = (
                    getattr(partner, 'direccion', False) or partner.street or False
                )
            else:
                rec.partner_ci = False
                rec.partner_celular = False
                rec.partner_telefono = False
                rec.partner_email = False
                rec.partner_direccion = False

    @api.depends(
        'tipo_ajuste_id', 'tipo_ajuste_id.enable_proration',
        'monto_prorrateo', 'monto_plan', 'monto_a_cobrar_manual',
        'monto_a_cobrar_manual_aplicado', 'es_primer_mes',
    )
    def _compute_monto_a_cobrar(self):
        """
        Compute the amount to charge (invoice amount) independently from payment status.
        This represents the billable amount for the billing period.
        Logic:
        1. If manual override is applied, use manual amount
        2. If adjustment type is set, use prorated amount if enabled, else use plan amount
        3. If first month, use prorated amount
        4. Otherwise, use plan amount
        
        IMPORTANT: This method should NEVER assign monto_pagado.
        Those are independent concepts:
        - monto_a_cobrar: What we bill to the customer
        - monto_pagado: What the customer actually paid (user input)
        """
        for rec in self:
            if rec.monto_a_cobrar_manual_aplicado:
                rec.monto_a_cobrar = rec.monto_a_cobrar_manual
            elif rec.tipo_ajuste_id:
                rec.monto_a_cobrar = (
                    rec.monto_prorrateo if rec.tipo_ajuste_id.enable_proration
                    else rec.monto_plan
                )
            elif rec.es_primer_mes:
                rec.monto_a_cobrar = rec.monto_prorrateo
            else:
                rec.monto_a_cobrar = rec.monto_plan

    def _inverse_monto_a_cobrar(self):
        for rec in self:
            rec.monto_a_cobrar_manual = rec.monto_a_cobrar
            rec.monto_a_cobrar_manual_aplicado = True

    @api.depends('monto_a_cobrar', 'monto_pagado', 'monto_prorrateo')
    def _compute_diferencia(self):
        for rec in self:
            rec.diferencia = rec.monto_pagado - rec.monto_a_cobrar

    @api.depends('comprobante_adjunto', 'comprobante_adjunto_fname')
    def _compute_comprobante_adjunto_type(self):
        for rec in self:
            name = (rec.comprobante_adjunto_fname or '').lower()
            is_image = bool(name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')))
            is_pdf = name.endswith('.pdf')

            if rec.comprobante_adjunto and not (is_image or is_pdf):
                try:
                    raw = base64.b64decode(rec.comprobante_adjunto)
                    if raw.startswith(b'%PDF'):
                        is_pdf = True
                    elif (
                        raw.startswith(b'\xff\xd8\xff')
                        or raw.startswith(b'\x89PNG\r\n\x1a\n')
                        or raw.startswith(b'GIF87a')
                        or raw.startswith(b'GIF89a')
                        or raw.startswith(b'RIFF')
                    ):
                        is_image = True
                except Exception:
                    pass

            rec.comprobante_adjunto_is_image = is_image
            rec.comprobante_adjunto_is_pdf = is_pdf

    # ── Due Date / Overdue ────────────────────────────────────
    @api.depends('anio', 'mes', 'contract_id')
    def _compute_fecha_vencimiento(self):
        for rec in self:
            if not rec.anio or not rec.mes:
                rec.fecha_vencimiento = False
                continue
            try:
                mes_int = int(rec.mes)
                anio_int = int(rec.anio)
                fecha_inicio_periodo = date(anio_int, mes_int, 1)

                if not rec.contract_id:
                    rec.fecha_vencimiento = fecha_inicio_periodo
                    continue

                regla = rec._get_regla_for_contract(rec.contract_id)
                if not regla:
                    rec.fecha_vencimiento = fecha_inicio_periodo
                    continue

                rec.fecha_vencimiento = self._calculate_due_date(
                    mes_int, anio_int, regla,
                )
            except Exception as e:
                _logger.warning(
                    f"Error computing fecha_vencimiento for payment {rec.id}: {e}"
                )
                rec.fecha_vencimiento = False

    def _compute_dias_atraso(self):
        hoy = date.today()
        for rec in self:
            if rec.fecha_vencimiento and rec.estado_pago not in ('pagado',):
                rec.dias_atraso = max((hoy - rec.fecha_vencimiento).days, 0)
            else:
                rec.dias_atraso = 0

    @api.depends('generado_automaticamente', 'estado_pago', 'fecha_vencimiento', 'mes', 'anio')
    def _compute_puede_marcar_mora_manual(self):
        hoy = fields.Date.context_today(self)
        for rec in self:
            rec.puede_marcar_mora_manual = False
            if rec.generado_automaticamente:
                continue
            if rec.estado_pago != 'pendiente':
                continue
            if not rec.fecha_vencimiento:
                continue

            try:
                mes_int = int(rec.mes)
                anio_int = int(rec.anio)
                periodo_inicio = date(anio_int, mes_int, 1)
            except Exception:
                continue

            inicio_mes_actual = date(hoy.year, hoy.month, 1)
            if periodo_inicio >= inicio_mes_actual:
                continue

            if hoy >= rec.fecha_vencimiento:
                rec.puede_marcar_mora_manual = True

    @api.depends('partner_id', 'periodo')
    def _compute_display_name(self):
        for rec in self:
            nombre = rec.partner_id.name or ''
            rec.display_name = f"{nombre} -- {rec.periodo}" if rec.periodo else nombre
    @api.depends('client_service_id.lead_id', 'contract_id.lead_id')
    def _compute_crm_data(self):
        for rec in self:
            lead = rec.client_service_id.lead_id or rec.contract_id.lead_id
            rec.crm_lead_id = lead
            rec.crm_zona = lead.zona if lead else False
            rec.crm_direccion = lead.direccion if lead else False
            rec.crm_ubicacion = lead.ubicacion if lead else False
            rec.crm_coordenadas = lead.coordenadas if lead else False

    # ── Receipt Computes ──────────────────────────────────────
    @api.depends()
    def _compute_recibo_id(self):
        Recibo = self.env['wigo.recibo.cobro']
        for rec in self:
            recibo = Recibo.sudo().search(
                [('pago_id', '=', rec.id), ('state', '!=', 'anulado')],
                limit=1, order='id DESC',
            )
            rec.recibo_id = recibo.id if recibo else False

    @api.depends('recibo_id')
    def _compute_recibo_generado(self):
        for rec in self:
            rec.recibo_generado = bool(rec.recibo_id)

    # ═══════════════════════════════════════════════════════════
    # Constraints
    # ═══════════════════════════════════════════════════════════

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
    @api.constrains('anio')
    def _check_anio(self):
        current_year = datetime.now().year

        for record in self:
            if not record.anio:
                continue

            # Solo números
            if not record.anio.isdigit():
                raise ValidationError(
                    "El año debe contener únicamente números."
                )

            # Exactamente 4 dígitos
            if len(record.anio) != 4:
                raise ValidationError(
                    "El año debe tener exactamente 4 dígitos."
                )

            year = int(record.anio)

            # Rango permitido
            if year < 2000 or year > current_year + 1:
                raise ValidationError(
                    f"El año debe estar entre 2000 y {current_year + 1}."
                )

    # ═══════════════════════════════════════════════════════════
    # Onchange
    # ═══════════════════════════════════════════════════════════

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

            rec.monto_a_cobrar = (
                rec.monto_prorrateo
                if (rec.tipo_ajuste_id and rec.tipo_ajuste_id.enable_proration) or rec.es_primer_mes
                else rec.monto_plan
            )
            rec.monto_pagado = rec.monto_a_cobrar or 0.0
            self._apply_default_amounts_onchange()

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

    # ═══════════════════════════════════════════════════════════
    # Defaults
    # ═══════════════════════════════════════════════════════════

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

        if not service_id and contract_id:
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

    # ═══════════════════════════════════════════════════════════
    # Create / Write
    # ═══════════════════════════════════════════════════════════

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
                vals['monto_prorrateo'] = 0.0 if not tipo_ajuste.enable_proration else vals.get('monto_prorrateo', 0.0)
                if not tipo_ajuste.requires_reason:
                    vals['motivo'] = False
                if tipo_ajuste.is_default:
                    vals['monto_a_cobrar_manual'] = 0.0
                    vals['monto_a_cobrar_manual_aplicado'] = False
            else:
                vals.setdefault('monto_prorrateo', 0.0)
                vals.setdefault('motivo', False)

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
                mes=vals.get('mes'),
                anio=vals.get('anio'),
            )
            if duplicate:
                raise ValidationError(
                    f"Ya existe un registro de cobro para el período {vals.get('mes')}/{vals.get('anio')} "
                    f"en el cliente o contrato seleccionado."
                )

            if vals.get('contract_id'):
                contract = Contract.browse(vals.get('contract_id'))
                vals['payment_mode'] = contract.payment_mode if contract and contract.payment_mode else False

            vals.setdefault('generado_automaticamente', False)

            vals['estado_pago'] = 'pendiente'

        records = super().create(vals_list)
        records._sync_payment_defaults()

        defaults = records.filtered(lambda r: r.tipo_ajuste_id and r.tipo_ajuste_id.is_default)
        if defaults:
            for rec in defaults:
                rec.with_context(
                    skip_sync_payment_defaults=True,
                    skip_payment_chatter=True,
                ).write(
                    {'monto_pagado': rec.monto_a_cobrar or 0.0}
                )

        for rec in records:
            rec._post_spanish_chatter_message(Markup(f"""
                <b>Registro de cobro creado</b><br/><br/>
                Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                Período: <b>{escape(rec.periodo or '')}</b><br/>
                Estado inicial: <b>{escape(dict(rec._fields['estado_pago'].selection).get(rec.estado_pago, rec.estado_pago or ''))}</b><br/>
                Monto a cobrar: <b>Bs. {rec.monto_a_cobrar:.2f}</b><br/>
                Monto pagado: <b>Bs. {rec.monto_pagado:.2f}</b><br/>
                Origen: <b>{'Generado automáticamente' if rec.generado_automaticamente else 'Creación manual'}</b>
            """))

        return records

    def write(self, vals):
        if self.env.context.get('skip_payment_chatter'):
            return super().write(vals)

        contable_fields = {'monto_a_cobrar', 'monto_pagado'}
        contable_changed = any(field in vals for field in contable_fields)
        payment_fields = {
            'estado_pago', 'canal_pago', 'fecha_pago', 'comprobante',
            'comprobante_adjunto', 'comprobante_attachment_ids',
        }
        payment_changed = any(field in vals for field in payment_fields)
        audit_payload = []

        if contable_changed or payment_changed:
            justificacion = (vals.get('justificacion_edicion') or '').strip()
            for rec in self:
                if contable_changed and rec.estado_pago in ('pagado', 'al_dia') and not justificacion:
                    raise ValidationError(
                        'Debe indicar una justificación para editar valores contables '
                        'cuando el pago ya fue confirmado (al día/pagado).'
                    )
                audit_payload.append({
                    'id': rec.id,
                    'old': {
                        'estado_pago': rec.estado_pago,
                        'monto_a_cobrar': rec.monto_a_cobrar,
                        'monto_pagado': rec.monto_pagado,
                        'canal_pago': rec.canal_pago,
                        'fecha_pago': rec.fecha_pago,
                        'comprobante': rec.comprobante,
                        'attachment_ids': rec.comprobante_attachment_ids.ids,
                        'attachment_names': rec.comprobante_attachment_ids.mapped('name'),
                    },
                    'justificacion': justificacion,
                    'usuario': self.env.user.display_name,
                    'fecha': self._get_bolivia_datetime_string(),
                })

        if 'tipo_ajuste_id' in vals:
            self._apply_tipo_ajuste_on_write(vals)
        elif 'es_primer_mes' in vals:
            self._apply_es_primer_mes_on_write(vals)

        res = super().write(vals)

        if contable_changed or payment_changed:
            for rec in self:
                payload = next((item for item in audit_payload if item['id'] == rec.id), None)
                if not payload:
                    continue
                nuevos = {
                    'estado_pago': rec.estado_pago,
                    'monto_a_cobrar': rec.monto_a_cobrar,
                    'monto_pagado': rec.monto_pagado,
                    'canal_pago': rec.canal_pago,
                    'fecha_pago': rec.fecha_pago,
                    'comprobante': rec.comprobante,
                    'attachment_ids': rec.comprobante_attachment_ids.ids,
                    'attachment_names': rec.comprobante_attachment_ids.mapped('name'),
                }
                state_changed = payload['old']['estado_pago'] != nuevos['estado_pago']
                if state_changed:
                    state_labels = dict(rec._fields['estado_pago'].selection)
                    rec._post_spanish_chatter_message(Markup(f"""
                        <b>Estado de cobro actualizado</b><br/><br/>
                        Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                        Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                        Período: <b>{escape(rec.periodo or '')}</b><br/>
                        Estado anterior: <b>{escape(state_labels.get(payload['old']['estado_pago'], payload['old']['estado_pago'] or ''))}</b><br/>
                        → nuevo: <b>{escape(state_labels.get(nuevos['estado_pago'], nuevos['estado_pago'] or ''))}</b><br/>
                        Usuario: <b>{escape(payload['usuario'] or '')}</b><br/>
                        Fecha: <b>{escape(payload['fecha'] or '')}</b>
                    """))

                if payload['old']['monto_a_cobrar'] != nuevos['monto_a_cobrar'] or payload['old']['monto_pagado'] != nuevos['monto_pagado']:
                    rec._post_spanish_chatter_message(Markup(f"""
                        <b>Actualización de valores contables registrada</b><br/><br/>
                        Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                        Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                        Período: <b>{escape(rec.periodo or '')}</b><br/>
                        Usuario: <b>{escape(payload['usuario'] or '')}</b><br/>
                        Fecha: <b>{escape(payload['fecha'] or '')}</b><br/><br/>
                        Monto a cobrar anterior: <b>Bs. {payload['old']['monto_a_cobrar']:.2f}</b><br/>
                        → nuevo: <b>Bs. {nuevos['monto_a_cobrar']:.2f}</b><br/>
                        Monto pagado anterior: <b>Bs. {payload['old']['monto_pagado']:.2f}</b><br/>
                        → nuevo: <b>Bs. {nuevos['monto_pagado']:.2f}</b><br/>
                        Justificación: <b>{escape(payload['justificacion'] or 'Sin justificación')}</b>
                    """))

                if (
                    payload['old']['canal_pago'] != nuevos['canal_pago']
                    or payload['old']['fecha_pago'] != nuevos['fecha_pago']
                    or payload['old']['comprobante'] != nuevos['comprobante']
                ):
                    rec._post_spanish_chatter_message(Markup(f"""
                        <b>Datos de pago actualizados</b><br/><br/>
                        Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                        Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                        Período: <b>{escape(rec.periodo or '')}</b><br/>
                        Canal de pago: <b>{escape(dict(rec._fields['canal_pago'].selection).get(payload['old']['canal_pago'], payload['old']['canal_pago'] or ''))}</b>
                        → <b>{escape(dict(rec._fields['canal_pago'].selection).get(nuevos['canal_pago'], nuevos['canal_pago'] or ''))}</b><br/>
                        Fecha de pago: <b>{escape(str(payload['old']['fecha_pago'] or ''))}</b>
                        → <b>{escape(str(nuevos['fecha_pago'] or ''))}</b><br/>
                        Comprobante: <b>{escape(payload['old']['comprobante'] or 'Sin referencia')}</b>
                        → <b>{escape(nuevos['comprobante'] or 'Sin referencia')}</b>
                    """))

                if payload['old']['attachment_ids'] != nuevos['attachment_ids']:
                    old_count = len(payload['old']['attachment_ids'])
                    new_count = len(nuevos['attachment_ids'])
                    added = [name for name in nuevos['attachment_names'] if name not in payload['old']['attachment_names']]
                    removed = [name for name in payload['old']['attachment_names'] if name not in nuevos['attachment_names']]
                    rec._post_spanish_chatter_message(Markup(f"""
                        <b>Archivo de comprobante actualizado</b><br/><br/>
                        Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                        Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                        Período: <b>{escape(rec.periodo or '')}</b><br/>
                        Archivos anteriores: <b>{old_count}</b><br/>
                        Archivos actuales: <b>{new_count}</b><br/>
                        Agregados: <b>{escape(', '.join(added) or 'Ninguno')}</b><br/>
                        Eliminados: <b>{escape(', '.join(removed) or 'Ninguno')}</b><br/>
                        La actualización del archivo quedó registrada correctamente en el historial.
                    """))

        if not self.env.context.get('skip_sync_payment_defaults') and any(
            k in vals for k in ('tipo_ajuste_id', 'es_primer_mes', 'monto_prorrateo', 'monto_plan', 'motivo')
        ):
            self._sync_payment_defaults()

        return res

    def _apply_tipo_ajuste_on_write(self, vals):
        tipo_ajuste = self.env['wigo.cobranza.tipo_ajuste'].browse(
            vals.get('tipo_ajuste_id')
        ) if vals.get('tipo_ajuste_id') else False
        if tipo_ajuste:
            vals['es_primer_mes'] = bool(tipo_ajuste.enable_proration)
            vals['monto_prorrateo'] = 0.0 if not tipo_ajuste.enable_proration else vals.setdefault('monto_prorrateo', 0.0)
            if not tipo_ajuste.requires_reason:
                vals['motivo'] = False
            if tipo_ajuste.is_default:
                vals['monto_a_cobrar_manual'] = 0.0
                vals['monto_a_cobrar_manual_aplicado'] = False
        else:
            vals['es_primer_mes'] = False
            vals['monto_prorrateo'] = 0.0
            vals['motivo'] = False

    def _apply_es_primer_mes_on_write(self, vals):
        if vals.get('es_primer_mes'):
            tipo_ajuste = self._get_legacy_proration_tipo_ajuste()
            if tipo_ajuste:
                vals['tipo_ajuste_id'] = tipo_ajuste.id
                vals['es_primer_mes'] = bool(tipo_ajuste.enable_proration)
                vals['monto_prorrateo'] = 0.0 if not tipo_ajuste.enable_proration else vals.setdefault('monto_prorrateo', 0.0)
                if not tipo_ajuste.requires_reason:
                    vals['motivo'] = False
        else:
            vals['monto_prorrateo'] = 0.0
            vals['motivo'] = False

    def _get_bolivia_datetime_string(self):
        now_dt = fields.Datetime.context_timestamp(
            self.with_context(tz='America/La_Paz'),
            fields.Datetime.now()
        )
        return now_dt.strftime('%Y-%m-%d %H:%M:%S')

    def _post_spanish_chatter_message(self, body, subtype_xmlid='mail.mt_note', partner_ids=None):
        self.ensure_one()
        self.with_context(lang='es_BO').message_post(
            body=body if isinstance(body, Markup) else Markup(body),
            subtype_xmlid=subtype_xmlid,
            partner_ids=partner_ids or False,
        )

    # ═══════════════════════════════════════════════════════════
    # Adjustment Helpers
    # ═══════════════════════════════════════════════════════════

    def _get_default_tipo_ajuste(self):
        TipoAjuste = self.env['wigo.cobranza.tipo_ajuste']
        return (
            TipoAjuste.search([('active', '=', True), ('is_default', '=', True)], limit=1)
            or TipoAjuste.search([('active', '=', True)], order='id asc', limit=1)
        )

    def _get_legacy_proration_tipo_ajuste(self):
        return self.env['wigo.cobranza.tipo_ajuste'].search([
            ('active', '=', True),
            ('enable_proration', '=', True),
        ], order='is_default desc, id asc', limit=1)

    def _sync_payment_defaults(self):
        if not self:
            return

        table = self._table
        for rec in self:
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

    # ═══════════════════════════════════════════════════════════
    # Contract / Service Helpers
    # ═══════════════════════════════════════════════════════════

    def _get_regla_for_contract(self, contract):
        Regla = self.env['wigo.cobranza.regla']
        if not contract:
            return Regla
        return Regla.search([
            ('active', '=', True),
            ('payment_mode', 'in', [contract.payment_mode, 'all']),
        ], order='sequence, id', limit=1)

    def _get_preferred_contract(self, partner):
        Contract = self.env['customer.contract']
        contracts = Contract.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active'),
        ], order='contract_date desc, id desc')
        return contracts[0] if contracts else False

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
        return svc or ClientService.search(
            [('partner_id', '=', contract.partner_id.id)], limit=1
        )

    def _find_contract_for_service(self, service):
        if not service:
            return False
        Contract = self.env['customer.contract']
        domain_base = [
            ('partner_id', '=', service.partner_id.id),
            ('state', '=', 'active'),
        ]

        if service.lead_id:
            contract = Contract.search(
                domain_base + [('lead_id', '=', service.lead_id.id)], limit=1
            )
            if contract:
                return contract

        contract = Contract.search(
            domain_base + [('name', '=', service.codigo_cliente)], limit=1
        )
        if contract:
            return contract

        if service.plan_id:
            contract = Contract.search(
                domain_base + [('plan_id', '=', service.plan_id.id)], limit=1
            )
            if contract:
                return contract

        return Contract.search(domain_base, order='contract_date desc, id desc', limit=1)

    # ═══════════════════════════════════════════════════════════
    # Business Actions
    # ═══════════════════════════════════════════════════════════

    def action_registrar_pago(self):
        for rec in self:
            if not rec.monto_pagado or not rec.fecha_pago:
                raise ValidationError(
                    'Debe ingresar el monto pagado y la fecha de pago antes de confirmar.'
                )
            if not rec.canal_pago:
                raise ValidationError('Debe seleccionar el canal de pago utilizado.')
            nuevo_estado = 'pagado' if rec.monto_pagado >= rec.monto_a_cobrar else 'pendiente'
            rec.with_context(skip_payment_chatter=True).write({
                'estado_pago': nuevo_estado,
                'registrado_por': self.env.user.id,
            })

            if rec.contract_id:
                self._update_incobrable_monto_cobrado(rec)

            svc = rec.client_service_id
            if svc:
                if nuevo_estado == 'pagado' and svc.estado_servicio == 'suspended':
                    svc.write({'estado_servicio': 'active'})
                    svc.with_context(lang='es_BO').message_post(
                        body=Markup(f"""
                            <b>Servicio reactivado por confirmación de pago</b><br/><br/>
                            Cliente: <b>{escape(svc.codigo_cliente or '')}</b><br/>
                            Nombre: <b>{escape(svc.partner_id.name or '')}</b><br/>
                            Monto pagado: <b>Bs. {rec.monto_pagado:.2f}</b><br/>
                            Período: <b>{escape(rec.periodo or '')}</b><br/><br/>
                            Se solicita verificar la reactivación técnica en la OLT.
                        """),
                        subtype_xmlid='mail.mt_comment',
                        partner_ids=self._get_tech_partner_ids(),
                    )

        rec._post_spanish_chatter_message(Markup(f"""
            <b>Pago confirmado</b><br/><br/>
            Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
            Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
            Período: <b>{escape(rec.periodo or '')}</b><br/>
            Canal de pago: <b>{escape(dict(rec._fields['canal_pago'].selection).get(rec.canal_pago, rec.canal_pago or ''))}</b><br/>
            Fecha de pago: <b>{escape(str(rec.fecha_pago or ''))}</b><br/>
            Monto a cobrar: <b>Bs. {rec.monto_a_cobrar:.2f}</b><br/>
            Monto pagado: <b>Bs. {rec.monto_pagado:.2f}</b><br/>
            Estado resultante: <b>{escape(dict(rec._fields['estado_pago'].selection).get(rec.estado_pago, rec.estado_pago or ''))}</b>
        """))
        return True

    def _update_incobrable_monto_cobrado(self, rec):
        Incobrable = self.env['wigo.incobrable']
        incobrables = Incobrable.search([
            ('contract_id', '=', rec.contract_id.id),
            ('state', 'not in', ['recuperado', 'baja_incobrable']),
        ])
        for incobrable in incobrables:
            incobrable.write({
                'monto_cobrado': incobrable.monto_cobrado + rec.monto_pagado,
            })

    def action_editar_valores_contables(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar valores contables',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': dict(
                self.env.context,
                contabilidad_editable=True,
                form_view_initial_mode='edit',
            ),
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

        if (
            self.contract_id
            and self.contract_id.lead_id
            and self.contract_id.lead_id.stage_id.is_won
        ):
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

    def action_marcar_mora(self):
        self.ensure_one()
        if not self.puede_marcar_mora_manual:
            raise UserError(
                'Solo se puede marcar en mora un pago creado manualmente y vencido '
                'correspondiente a un período anterior.'
            )

        self.with_context(skip_payment_chatter=True).write({'estado_pago': 'mora'})

        self._post_spanish_chatter_message(Markup(f"""
            <b>Registro marcado manualmente en mora</b><br/><br/>
            Cliente: <b>{escape(self.partner_id.display_name or self.partner_id.name or '')}</b><br/>
            Contrato: <b>{escape(self.contract_id.display_name or self.contract_id.name or '')}</b><br/>
            Período: <b>{escape(self.periodo or '')}</b><br/>
            Fecha de vencimiento: <b>{escape(str(self.fecha_vencimiento or ''))}</b><br/>
            Observación: el estado fue actualizado manualmente por un usuario autorizado.
        """))

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_instruir_baja(self):
        for rec in self:
            rec.with_context(skip_payment_chatter=True).write({'estado_pago': 'baja_definitiva'})
            svc = rec.client_service_id
            if svc:
                svc.write({
                    'estado_pago': 'baja_definitiva',
                    'estado_servicio': 'baja',
                    'fecha_baja': fields.Date.context_today(self.with_context(tz='America/La_Paz')),
                })
                svc.with_context(lang='es_BO').message_post(
                    body=Markup(f"""
                        <b>Baja definitiva instruida por cobranza</b><br/><br/>
                        Cliente: <b>{escape(svc.codigo_cliente or '')}</b><br/>
                        Nombre: <b>{escape(svc.partner_id.name or '')}</b><br/>
                        Período: <b>{escape(rec.periodo or '')}</b><br/><br/>
                        Área técnica: retirar equipo ONU y actualizar el estado del servicio en el sistema.
                    """),
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=self._get_tech_partner_ids(),
                )
            rec._post_spanish_chatter_message(Markup(f"""
                <b>Registro marcado para baja definitiva</b><br/><br/>
                Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                Período: <b>{escape(rec.periodo or '')}</b><br/>
                Estado final: <b>{escape(dict(rec._fields['estado_pago'].selection).get(rec.estado_pago, rec.estado_pago or ''))}</b><br/>
                Se dejó constancia de la instrucción para baja definitiva.
            """))

    def unlink(self):
        for rec in self:
            rec._post_spanish_chatter_message(Markup(f"""
                <b>Registro de cobro eliminado</b><br/><br/>
                Cliente: <b>{escape(rec.partner_id.display_name or rec.partner_id.name or '')}</b><br/>
                Contrato: <b>{escape(rec.contract_id.display_name or rec.contract_id.name or '')}</b><br/>
                Período: <b>{escape(rec.periodo or '')}</b><br/>
                Estado previo: <b>{escape(dict(rec._fields['estado_pago'].selection).get(rec.estado_pago, rec.estado_pago or ''))}</b><br/>
                Esta eliminación quedó registrada como trazabilidad antes de retirar el registro del sistema.
            """))
        return super().unlink()

    # ═══════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════

    def _get_tech_partner_ids(self):
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

    # ═══════════════════════════════════════════════════════════
    # Receipt Actions
    # ═══════════════════════════════════════════════════════════

    def _get_or_create_recibo(self):
        self.ensure_one()
        Recibo = self.env['wigo.recibo.cobro']
        recibo = Recibo.search(
            [('pago_id', '=', self.id), ('state', '!=', 'anulado')],
            limit=1, order='id DESC',
        )
        if not recibo:
            recibo = Recibo.create({'pago_id': self.id})
        return recibo

    def action_generar_recibo(self):
        self.ensure_one()
        if self.estado_pago not in ('pagado', 'pendiente'):
            raise UserError(
                'Solo se puede generar recibo para pagos confirmados (Pagado o Pendiente).'
            )
        recibo = self._get_or_create_recibo()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Recibo -- {self.display_name}',
            'res_model': 'wigo.recibo.cobro',
            'view_mode': 'form',
            'res_id': recibo.id,
            'target': 'current',
        }

    def action_abrir_recibo(self):
        self.ensure_one()
        recibo = self.env['wigo.recibo.cobro'].search(
            [('pago_id', '=', self.id), ('state', '!=', 'anulado')],
            limit=1, order='id DESC',
        )
        if not recibo:
            return self.action_generar_recibo()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Recibo -- {self.display_name}',
            'res_model': 'wigo.recibo.cobro',
            'view_mode': 'form',
            'res_id': recibo.id,
            'target': 'current',
        }

    def action_imprimir_recibo(self):
        self.ensure_one()
        recibo = self._get_or_create_recibo()
        return recibo.action_imprimir()

    # ═══════════════════════════════════════════════════════════
    # Invoice Actions
    # ═══════════════════════════════════════════════════════════

    def action_registrar_factura(self):
        self.ensure_one()
        Factura = self.env['wigo.factura.cobranza']
        factura = Factura.search(
            [('pago_id', '=', self.id), ('state', '!=', 'anulada')], limit=1
        )
        ctx = {
            'default_pago_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_contract_id': self.contract_id.id if self.contract_id else False,
            'default_monto_total': self.monto_pagado,
            'default_periodo_facturado': self.periodo,
            'default_fecha_emision': str(
                self.fecha_pago or fields.Date.context_today(self)
            ),
        }
        return {
            'type': 'ir.actions.act_window',
            'name': f'Factura -- {self.display_name}',
            'res_model': 'wigo.factura.cobranza',
            'view_mode': 'form',
            'views': [(
                self.env.ref('wigo_cobranza.view_invoice_form_emit').id, 'form'
            )],
            'res_id': factura.id if factura else False,
            'target': 'new',
            'context': ctx,
        }

    # ═══════════════════════════════════════════════════════════
    # Navigation
    # ═══════════════════════════════════════════════════════════

    def action_open_partner(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.partner_id.name,
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
        }

    # ═══════════════════════════════════════════════════════════
    # Legacy Cron Aliases
    # ═══════════════════════════════════════════════════════════

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

    @api.model
    def cron_detectar_incobrables(self):
        return self.cron_procesar_cobranza()

    @api.model
    def cron_alertar_suspension(self):
        return self.cron_procesar_cobranza()
