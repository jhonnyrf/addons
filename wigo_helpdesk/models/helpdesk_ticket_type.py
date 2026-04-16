# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskTicketType(models.Model):
    _name = 'helpdesk.ticket.type'
    _description = 'Tipo de Ticket'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Código',
        required=True,
        help='Código interno para el tipo de ticket (ej: incident, request)',
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    description = fields.Text(
        string='Descripción',
        translate=True,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    ticket_count = fields.Integer(
        string='Tickets',
        compute='_compute_ticket_count',
        store=False,
    )

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            [('ticket_type_id', 'in', self.ids)],
            groupby=['ticket_type_id'],
            aggregates=['__count'],
        )
        mapped = {type_id.id: count for type_id, count in ticket_data}
        for ticket_type in self:
            ticket_type.ticket_count = mapped.get(ticket_type.id, 0)
