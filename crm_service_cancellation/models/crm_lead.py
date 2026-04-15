# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    cancellation_ids = fields.One2many(
        'service.cancellation',
        'lead_id',
        string='Bajas de servicio',
    )
    cancellation_count = fields.Integer(
        string='Bajas',
        compute='_compute_cancellation_count',
        store=False,
    )
    has_cancellation = fields.Boolean(
        string='¿Tiene baja registrada?',
        compute='_compute_has_cancellation',
        store=True,
    )

    @api.depends('cancellation_ids')
    def _compute_cancellation_count(self):
        for lead in self:
            lead.cancellation_count = len(lead.cancellation_ids)

    @api.depends('cancellation_ids')
    def _compute_has_cancellation(self):
        for lead in self:
            lead.has_cancellation = bool(lead.cancellation_ids)

    def action_open_cancellation_wizard(self):
        self.ensure_one()

        # Intentar obtener CI desde el contrato o desde el partner
        ci = ''
        if self.contract_id and self.contract_id.ci:
            ci = self.contract_id.ci
        elif self.partner_id and hasattr(self.partner_id, 'ci'):
            ci = self.partner_id.ci or ''

        return {
            'type': 'ir.actions.act_window',
            'name': 'Baja de Servicio',
            'res_model': 'service.cancellation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id':        self.id,
                'default_partner_id':     self.partner_id.id if self.partner_id else False,
                'default_contract_id':    self.contract_id.id if self.contract_id else False,
                'default_codigo_cliente': self.codigo_cliente or '',
                'default_ci_cliente':     ci,
                'default_plan_id':        self.plan_id.id if self.plan_id else False,
            },
        }

    def action_view_cancellations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bajas de servicio',
            'res_model': 'service.cancellation',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id':    self.id,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }
