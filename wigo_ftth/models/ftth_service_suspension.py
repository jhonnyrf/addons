# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FtthServiceSuspension(models.Model):
    _name = 'wigo.ftth.service.suspension'
    _description = 'Registro de suspensión FTTH'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_registro desc, id desc'
    _rec_name = 'display_name'

    name = fields.Char(string='Referencia', readonly=True, copy=False, default='Nueva Suspensión')
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='contract_id.partner_id',
        store=True,
        readonly=True,
    )
    contract_id = fields.Many2one(
        'customer.contract',
        string='Contrato',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True,
    )
    client_service_id = fields.Many2one(
        'wigo.ftth.client.service',
        string='Ficha técnica',
        tracking=True,
        index=True,
        ondelete='set null',
        domain="[('partner_id', '=', partner_id)]",
    )
    fecha_registro = fields.Datetime(
        string='Fecha de creación del registro',
        default=fields.Datetime.now,
        readonly=True,
        copy=False,
        tracking=True,
    )
    fecha_corte = fields.Date(string='Fecha de corte', tracking=True)
    fecha_reconexion = fields.Date(string='Fecha de reconexión', tracking=True)
    state = fields.Selection(
        [
            ('pendiente', 'Pendiente'),
            ('in_cut', 'En corte'),
            ('reconexion', 'Reconexión'),
        ],
        string='Estado',
        default='pendiente',
        required=True,
        tracking=True,
        index=True,
    )
    display_name = fields.Char(compute='_compute_display_name', store=True)
    incobrable_count = fields.Integer(compute='_compute_incobrable_count', store=False)

    @api.depends('contract_id', 'state', 'fecha_corte', 'fecha_reconexion')
    def _compute_display_name(self):
        for record in self:
            contract = record.contract_id.name or 'Sin contrato'
            state = dict(record._fields['state'].selection).get(record.state, record.state or '')
            record.display_name = f'{contract} — {state}'.strip(' —')

    def _compute_incobrable_count(self):
        Incobrable = self.env.registry.get('wigo.incobrable') and self.env['wigo.incobrable'] or False
        for record in self:
            if not Incobrable:
                record.incobrable_count = 0
                continue
            domain = [('suspension_id', '=', record.id)]
            record.incobrable_count = Incobrable.search_count(domain)

    def _ensure_cut_date(self):
        self.ensure_one()
        if not self.fecha_corte:
            self.fecha_corte = date.today()

    def action_marcar_en_corte(self):
        for record in self:
            record.state = 'in_cut'
            record._ensure_cut_date()
            # Actualizar estado de la ficha técnica
            if record.client_service_id:
                record.client_service_id.estado_servicio = 'corte'

    def action_marcar_reconexion(self):
        for record in self:
            record.state = 'reconexion'
            if not record.fecha_reconexion:
                record.fecha_reconexion = date.today()
            # Actualizar estado de la ficha técnica
            if record.client_service_id:
                record.client_service_id.estado_servicio = 'active'

    def action_view_incobrables(self):
        self.ensure_one()
        Incobrable = self.env.registry.get('wigo.incobrable') and self.env['wigo.incobrable'] or False
        if not Incobrable:
            raise ValidationError('No está disponible el módulo de incobrables en esta base de datos.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incobrables relacionados',
            'res_model': 'wigo.incobrable',
            'view_mode': 'list,form',
            'domain': [('suspension_id', '=', self.id)],
            'context': {
                'default_contract_id': self.contract_id.id,
                'default_client_service_id': self.client_service_id.id if self.client_service_id else False,
            },
        }

    def action_view_client_service(self):
        self.ensure_one()
        if not self.client_service_id:
            raise ValidationError('No existe una ficha técnica vinculada a esta suspensión.')
        return {
            'type': 'ir.actions.act_window',
            'name': self.client_service_id.display_name,
            'res_model': 'wigo.ftth.client.service',
            'view_mode': 'form',
            'res_id': self.client_service_id.id,
            'target': 'current',
        }
