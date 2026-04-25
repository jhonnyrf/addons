# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WigoIncobrable(models.Model):
    """
    Registro de deudas declaradas incobrables por Contabilidad.
    Un cliente puede tener varios registros (uno por período adeudado).
    """
    _name = 'wigo.incobrable'
    _description = 'Deuda Incobrable'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_declaracion desc'
    _rec_name = 'display_name'

    # ── Identificación ───────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict', tracking=True, index=True,
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
        tracking=True,
    )
    client_service_id = fields.Many2one(
        'wigo.ftth.client.service', string='Servicio (CF)',
        ondelete='restrict', tracking=True,
    )
    codigo_cliente = fields.Char(
        string='Código CF',
        compute='_compute_datos_cliente', store=True,
    )
    plan_id = fields.Many2one(
        'internet.plan', string='Plan',
        compute='_compute_datos_cliente', store=True,
    )

    # ── Deuda ────────────────────────────────────────────────────
    meses_adeudados = fields.Char(
        string='Meses adeudados',
        help='Ej: Enero, Febrero/2026',
        tracking=True,
    )
    monto_total_adeudado = fields.Float(
        string='Monto total adeudado (Bs)',
        tracking=True,
    )
    monto_condonado = fields.Float(
        string='Monto condonado (Bs)',
        tracking=True,
    )
    monto_cobrado = fields.Float(
        string='Monto cobrado efectivamente (Bs)',
        tracking=True,
    )
    diferencia_incobrable = fields.Float(
        string='Monto incobrable definitivo (Bs)',
        compute='_compute_diferencia_incobrable', store=True,
    )

    # ── Estado y fechas ──────────────────────────────────────────
    fecha_declaracion = fields.Date(
        string='Fecha de declaración',
        default=lambda self: fields.Date.context_today(self),
        required=True, tracking=True,
    )
    fecha_baja_servicio = fields.Date(
        string='Fecha baja de servicio', tracking=True,
    )
    equipo_retirado = fields.Boolean(
        string='Equipo ONU retirado', tracking=True,
    )
    fecha_retiro_equipo = fields.Date(
        string='Fecha retiro equipo', tracking=True,
    )
    state = fields.Selection([
        ('activo', 'En gestión'),       # todavía hay esperanza
        ('baja_incobrable', 'Baja - Incobrable'),
        ('recuperado', 'Recuperado'),    # pagó después
        ('condonado', 'Condonado'),
    ], string='Estado', default='activo', required=True, tracking=True, index=True)

    # ── Observaciones ────────────────────────────────────────────
    observaciones = fields.Text(string='Observaciones')

    # ── Display ──────────────────────────────────────────────────
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('partner_id', 'contract_id', 'client_service_id')
    def _compute_datos_cliente(self):
        for rec in self:
            rec.codigo_cliente = (
                rec.contract_id.name or
                rec.client_service_id.codigo_cliente or
                False
            )
            rec.plan_id = (
                rec.contract_id.plan_id or
                rec.client_service_id.plan_id or
                False
            )

    @api.depends('monto_total_adeudado', 'monto_condonado', 'monto_cobrado')
    def _compute_diferencia_incobrable(self):
        for rec in self:
            rec.diferencia_incobrable = (
                rec.monto_total_adeudado -
                rec.monto_condonado -
                rec.monto_cobrado
            )

    @api.depends('partner_id', 'meses_adeudados')
    def _compute_display_name(self):
        for rec in self:
            nombre = rec.partner_id.name or ''
            rec.display_name = f"{nombre} — {rec.meses_adeudados}" if rec.meses_adeudados else nombre

    def action_marcar_baja_incobrable(self):
        for rec in self:
            rec.state = 'baja_incobrable'
            if not rec.fecha_baja_servicio:
                rec.fecha_baja_servicio = date.today()
            # Marcar el servicio como baja si existe
            if rec.client_service_id:
                rec.client_service_id.estado_pago = 'baja_definitiva'
                if rec.client_service_id.estado_servicio != 'baja':
                    rec.client_service_id.estado_servicio = 'baja'
                    rec.client_service_id.fecha_baja = date.today()

    def action_marcar_recuperado(self):
        for rec in self:
            rec.state = 'recuperado'

    def action_marcar_condonado(self):
        for rec in self:
            rec.state = 'condonado'

    @api.model
    def crear_desde_pago_mora(self, pago_estado):
        """
        Crea un registro incobrable a partir de un pago en mora.
        Llamado desde la acción de baja definitiva del pago.
        """
        existing = self.search([
            ('partner_id', '=', pago_estado.partner_id.id),
            ('contract_id', '=', pago_estado.contract_id.id),
            ('state', 'not in', ['recuperado', 'condonado']),
        ], limit=1)
        if existing:
            return existing

        return self.create({
            'partner_id': pago_estado.partner_id.id,
            'contract_id': pago_estado.contract_id.id,
            'client_service_id': pago_estado.client_service_id.id or False,
            'meses_adeudados': pago_estado.periodo,
            'monto_total_adeudado': pago_estado.monto_a_cobrar,
            'state': 'activo',
        })
