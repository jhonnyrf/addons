# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PartnerPlan(models.Model):
    """
    Plan de internet contratado por un cliente (res.partner).
    Un cliente puede tener N planes, cada uno con su código CF-XXX único,
    su estado y sus fechas de inicio/baja.
    Se crea automáticamente cuando se gana un lead en el CRM.
    """
    _name = 'partner.plan'
    _description = 'Plan Contratado del Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'
    _rec_name = 'codigo_cliente'

    # ── Relación con el contacto ──────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ── Plan de internet ──────────────────────────────────────────
    plan_id = fields.Many2one(
        'internet.plan',
        string='Plan',
        required=True,
        domain="[('active', '=', True)]",
        tracking=True,
    )
    plan_type = fields.Selection(
        related='plan_id.plan_type',
        string='Tipo',
        store=True,
    )
    plan_price = fields.Float(
        related='plan_id.price',
        string='Tarifa (Bs)',
        store=True,
    )

    # ── Código único CF-XXX ───────────────────────────────────────
    codigo_cliente = fields.Char(
        string='Código CF',
        required=True,
        copy=False,
        tracking=True,
        help='Formato: CF-001, CF-023, etc. Único en todo el sistema.',
        index=True,
    )

    # ── Estado ────────────────────────────────────────────────────
    state = fields.Selection([
        ('active',    'Activo'),
        ('suspended', 'Suspendido'),
        ('cancelled', 'Dado de baja'),
    ], string='Estado', default='active', required=True, tracking=True)

    # ── Fechas ────────────────────────────────────────────────────
    date_start = fields.Date(
        string='Fecha de inicio',
        required=True,
        default=fields.Date.today,
    )
    date_end = fields.Date(
        string='Fecha de baja',
        readonly=True,
        tracking=True,
    )

    # ── Origen: lead del CRM que generó este contrato ─────────────
    lead_id = fields.Many2one(
        'crm.lead',
        string='Oportunidad origen',
        help='Lead del CRM que originó este contrato (se llena automáticamente al ganar).',
        ondelete='set null',
    )

    # ── Datos de instalación ──────────────────────────────────────
    zona      = fields.Char(string='Zona')
    direccion = fields.Char(string='Dirección')
    ubicacion = fields.Char(string='Ubicación (Google Maps)', help='Enlace de Google Maps')
    notes     = fields.Text(string='Notas')

    # ── Constrains ────────────────────────────────────────────────

    @api.constrains('codigo_cliente')
    def _check_codigo_cliente(self):
        for rec in self:
            if not rec.codigo_cliente:
                continue
            codigo = rec.codigo_cliente.strip().upper()
            if not re.match(r'^CF-\d+$', codigo):
                raise ValidationError(
                    "El código debe tener el formato CF-001, CF-023, etc."
                )
            dup = self.search([
                ('codigo_cliente', '=ilike', codigo),
                ('id', '!=', rec.id),
            ], limit=1)
            if dup:
                raise ValidationError(
                    f"El código '{codigo}' ya está asignado a "
                    f"'{dup.partner_id.name}'."
                )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    "La fecha de baja no puede ser anterior a la de inicio."
                )

    # ── Transiciones de estado ───────────────────────────────────

    def action_suspend(self):
        for rec in self:
            if rec.state != 'active':
                raise ValidationError("Solo se puede suspender un plan activo.")
            rec.write({'state': 'suspended'})

    def action_reactivate(self):
        for rec in self:
            if rec.state not in ('suspended', 'cancelled'):
                raise ValidationError("El plan no está suspendido ni cancelado.")
            rec.write({'state': 'active', 'date_end': False})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'cancelled':
                raise ValidationError("El plan ya está dado de baja.")
            rec.write({'state': 'cancelled', 'date_end': fields.Date.today()})
