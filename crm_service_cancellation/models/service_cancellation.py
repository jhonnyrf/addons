# -*- coding: utf-8 -*-
from odoo import models, fields, api


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

    # ─── Datos del ONU (estáticos, sin conexión aún) ─────────────────────────
    onu_serial = fields.Char(string='N° de serie ONU')
    onu_mac = fields.Char(string='MAC ONU')
    onu_modelo = fields.Char(string='Modelo ONU')

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
