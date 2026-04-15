# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskStage(models.Model):
    _name = 'helpdesk.stage'
    _description = 'Etapa del Ticket'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    description = fields.Text(
        string='Descripción',
        translate=True,
    )
    fold = fields.Boolean(
        string='Plegado en Kanban',
        default=False,
    )
    is_close = fields.Boolean(
        string='Etapa de Cierre',
        default=False,
        help='Los tickets en esta etapa se consideran cerrados/resueltos.',
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    ticket_count = fields.Integer(
        string='Tickets',
        compute='_compute_ticket_count',
    )

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            [('stage_id', 'in', self.ids)],
            groupby=['stage_id'],
            aggregates=['__count'],
        )
        mapped = {stage.id: count for stage, count in ticket_data}
        for stage in self:
            stage.ticket_count = mapped.get(stage.id, 0)
