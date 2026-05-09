# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ServiceCancellation(models.Model):
    """
    Registro histórico permanente de bajas de servicio.
    Se crea cuando el agente confirma la baja desde el wizard.
    """
    _name = 'service.cancellation'
    _description = 'Baja de Servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'fecha_baja desc, id desc'

    # ─── Relaciones principales ───────────────────────────────────────────────
    lead_id = fields.Many2one(
        'crm.lead',
        string='Oportunidad CRM',
        readonly=True,
        ondelete='set null',
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
    )
    contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato',
        readonly=True,
        ondelete='set null',
        tracking=True,
    )

    # ─── Datos del cliente ────────────────────────────────────────────────────
    codigo_cliente = fields.Char(string='Código de cliente', tracking=True)
    ci_cliente = fields.Char(string='Carnet de identidad', tracking=True)
    plan_id = fields.Many2one('internet.plan', string='Plan contratado', readonly=True)

    # ─── Motivo de baja (catálogo editable) ──────────────────────────────────
    reason_id = fields.Many2one(
        'crm.cancellation.reason',
        string='Motivo de baja',
        required=True,
        tracking=True,
    )
    motivo_detalle = fields.Text(
        string='Detalle del motivo',
        help='Información adicional sobre el motivo de baja',
    )
    fecha_baja = fields.Date(string='Fecha de baja', required=True, tracking=True)

    # ─── Datos técnicos FTTH (snapshot al momento de la baja) ────────────────
    ftth_client_service_id = fields.Many2one(
        'wigo.ftth.client.service',
        string='Ficha técnica FTTH',
        readonly=True,
        tracking=True,
    )
    ftth_estado_servicio = fields.Selection(
        [
            ('active', 'Activo'),
            ('suspended', 'Suspendido'),
            ('corte', 'En corte (mora)'),
            ('baja', 'Dado de baja'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado servicio FTTH',
        tracking=True,
    )
    ftth_fecha_instalacion = fields.Date(string='Fecha instalación FTTH')
    ftth_nodo = fields.Char(string='Nodo FTTH')
    ftth_olt = fields.Char(string='OLT FTTH')
    ftth_olt_port = fields.Char(string='Puerto OLT FTTH')
    ftth_subinterface = fields.Char(string='Subinterfaz FTTH')
    ftth_nap = fields.Char(string='NAP FTTH')
    ftth_nap_port = fields.Char(string='Puerto NAP FTTH')

    # ─── Datos del ONU (autocompletados desde FTTH) ──────────────────────────
    onu_equipo = fields.Char(string='Equipo')
    onu_rotulo = fields.Char(string='Rótulo / Etiqueta')
    onu_marca = fields.Char(string='Marca')
    onu_serial = fields.Char(string='N° de serie ONU')
    onu_mac = fields.Char(string='MAC ONU')
    onu_modelo = fields.Char(string='Modelo ONU')

    cobranza_estado_pago = fields.Selection(
        [
            ('pagado', 'Cobrado / Al día'),
            ('pendiente', 'Pendiente'),
            ('mora', 'En mora'),
        ],
        string='Estado de cobranza',
        tracking=True,
    )
    cobranza_ultimo_periodo_pagado = fields.Char(string='Último mes pagado')
    cobranza_ultimo_pago_fecha = fields.Date(string='Fecha de pago')
    cobranza_ultimo_monto_pagado = fields.Monetary(string='Monto pagado', currency_field='currency_id')
    
    cobranza_monto_deuda_total = fields.Monetary(string='Monto que debe', currency_field='currency_id')
    cobranza_dias_retraso = fields.Integer(string='Días de retraso')

    # ─── Deuda ───────────────────────────────────────────────────────────────
    meses_deuda = fields.Integer(string='Meses de deuda', default=0)
    deuda_pendiente = fields.Boolean(
        string='Tiene deuda',
        compute='_compute_deuda_pendiente',
        store=True,
    )
    monto_deuda = fields.Monetary(string='Monto de deuda', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends('meses_deuda')
    def _compute_deuda_pendiente(self):
        for rec in self:
            rec.deuda_pendiente = rec.meses_deuda > 0

    # ─── Contrato ─────────────────────────────────────────────────────────────
    contrato_terminado = fields.Boolean(string='Contrato terminado', tracking=True)
    contract_state_at_cancellation = fields.Char(
        string='Estado del contrato al dar de baja',
        readonly=True,
    )

    # ─── Control interno ─────────────────────────────────────────────────────
    registrado_reporte = fields.Boolean(
        string='Registrado en reporte',
        default=False,
        tracking=True,
    )
    notas = fields.Text(string='Notas internas')

    # ─── Display name ─────────────────────────────────────────────────────────
    display_name = fields.Char(
        string='Nombre',
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('partner_id', 'fecha_baja', 'codigo_cliente')
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.partner_id:
                parts.append(rec.partner_id.name)
            if rec.codigo_cliente:
                parts.append(f'[{rec.codigo_cliente}]')
            if rec.fecha_baja:
                parts.append(rec.fecha_baja.strftime('%d/%m/%Y'))
            rec.display_name = ' - '.join(parts) if parts else 'Baja sin nombre'

    def action_open_ftth_service(self):
        self.ensure_one()
        service = self.ftth_client_service_id
        if not service:
            raise UserError('No hay ficha FTTH vinculada a esta baja.')
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ficha FTTH - {service.codigo_cliente or service.partner_id.name}',
            'res_model': 'wigo.ftth.client.service',
            'view_mode': 'form',
            'res_id': service.id,
            'target': 'current',
        }

    def action_open_cobranza_payments(self):
        self.ensure_one()
        domain = []
        if self.ftth_client_service_id:
            domain = [('client_service_id', '=', self.ftth_client_service_id.id)]
        elif self.contract_id:
            domain = [('contract_id', '=', self.contract_id.id)]
        elif self.partner_id:
            domain = [('partner_id', '=', self.partner_id.id)]

        if not domain:
            raise UserError('No hay referencia de cliente/contrato/servicio para abrir pagos de cobranza.')

        list_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_list_new', raise_if_not_found=False)
        form_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_form_new', raise_if_not_found=False)
        views = []
        if list_view:
            views.append((list_view.id, 'list'))
        if form_view:
            views.append((form_view.id, 'form'))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Cobranza - {self.partner_id.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'views': views or False,
            'domain': domain,
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contract_id': self.contract_id.id if self.contract_id else False,
                'default_client_service_id': self.ftth_client_service_id.id if self.ftth_client_service_id else False,
                'search_default_filter_mora': 0,
            },
            'target': 'current',
        }
