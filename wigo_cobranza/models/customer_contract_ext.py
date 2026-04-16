# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api
from odoo.exceptions import UserError


class CustomerContractCobranza(models.Model):
    _inherit = 'customer.contract'

    pago_estado_ids = fields.One2many(
        'wigo.pago.estado',
        'contract_id',
        string='Cobros mensuales',
    )
    unpaid_month_count = fields.Integer(
        string='Meses sin pagar',
        compute='_compute_unpaid_month_count',
    )

    @api.depends('pago_estado_ids.estado_pago')
    def _compute_unpaid_month_count(self):
        for contract in self:
            contract.unpaid_month_count = len(
                contract.pago_estado_ids.filtered(
                    lambda p: p.estado_pago in ('pendiente', 'deuda_parcial', 'mora')
                )
            )

    def action_view_cobranza_mensual(self):
        self.ensure_one()
        list_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_list_new', raise_if_not_found=False)
        form_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_form_new', raise_if_not_found=False)
        views = []
        if list_view:
            views.append((list_view.id, 'list'))
        if form_view:
            views.append((form_view.id, 'form'))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Cobranza mensual - {self.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'views': views or False,
            'target': 'current',
            'domain': [('contract_id', '=', self.id)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contract_id': self.id,
                'default_client_service_id': False,
                'create': True,
                'show_create': True,
            },
        }

    def action_crear_pago_mes_contrato(self):
        self.ensure_one()
        today = date.today()
        form_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_form_new', raise_if_not_found=False)
        return {
            'type': 'ir.actions.act_window',
            'name': f'Nuevo registro mensual - {self.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'form',
            'views': [(form_view.id, 'form')] if form_view else False,
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contract_id': self.id,
                'default_client_service_id': False,
                'default_mes': str(today.month),
                'default_anio': today.year,
            },
        }

    def action_open_contract_full(self):
        self.ensure_one()
        lead = self._get_won_crm_lead()
        if not lead:
            raise UserError('No se encontro un ticket CRM en estado ganado para este contrato.')

        return {
            'type': 'ir.actions.act_window',
            'name': f'Ticket CRM - {self.name}',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': lead.id,
            'target': 'current',
        }

    def _get_won_crm_lead(self):
        self.ensure_one()
        Lead = self.env['crm.lead']

        if self.lead_id and self.lead_id.stage_id.is_won:
            return self.lead_id

        lead = Lead.search([
            ('contract_id', '=', self.id),
            ('stage_id.is_won', '=', True),
        ], order='write_date desc, id desc', limit=1)
        if lead:
            return lead

        return Lead.search([
            ('partner_id', '=', self.partner_id.id),
            ('stage_id.is_won', '=', True),
        ], order='write_date desc, id desc', limit=1)
