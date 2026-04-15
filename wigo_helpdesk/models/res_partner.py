# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartnerHelpdesk(models.Model):
    _inherit = 'res.partner'

    helpdesk_ticket_ids = fields.One2many(
        comodel_name='helpdesk.ticket',
        inverse_name='partner_id',
        string='Tickets Helpdesk',
        help='Tickets asociados a este contacto.',
    )
    helpdesk_ticket_count = fields.Integer(
        string='Tickets',
        compute='_compute_helpdesk_ticket_count',
        search='_search_helpdesk_ticket_count',
    )

    @api.model
    def _get_helpdesk_ticket_count_map(self):
        ticket_model = self.env['helpdesk.ticket']
        count_map = {}
        for ticket in ticket_model.search([]):
            partner = ticket.partner_id.commercial_partner_id
            if not partner and ticket.contract_id and ticket.contract_id.partner_id:
                partner = ticket.contract_id.partner_id.commercial_partner_id
            if partner:
                count_map[partner.id] = count_map.get(partner.id, 0) + 1
        return count_map

    def _compute_helpdesk_ticket_count(self):
        count_map = self._get_helpdesk_ticket_count_map()
        for partner in self:
            partner.helpdesk_ticket_count = count_map.get(partner.commercial_partner_id.id, 0)

    def _search_helpdesk_ticket_count(self, operator, value):
        if operator not in ('=', '!=', '>', '>=', '<', '<='):
            return [('id', '=', 0)]

        count_map = self._get_helpdesk_ticket_count_map()
        target = int(value or 0)
        partner_ids = []
        for partner_id, count in count_map.items():
            matches = {
                '=': count == target,
                '!=': count != target,
                '>': count > target,
                '>=': count >= target,
                '<': count < target,
                '<=': count <= target,
            }.get(operator, False)
            if matches:
                partner_ids.append(partner_id)
        return [('id', 'in', partner_ids or [0])]
