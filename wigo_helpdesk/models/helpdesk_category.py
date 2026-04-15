# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskCategory(models.Model):
    _name = 'helpdesk.category'
    _description = 'Categoría del Ticket'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Código',
        size=10,
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    description = fields.Text(
        string='Descripción',
        translate=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )
    # Área responsable de esta categoría
    area = fields.Selection(
        selection=[
            ('technical', 'Área Técnica'),
            ('commercial', 'Área Comercial'),
            ('both', 'Ambas Áreas'),
        ],
        string='Área Responsable',
        default='technical',
        required=True,
    )
    # SLA específico por categoría (en horas), 0 = usa el del ticket
    sla_hours = fields.Float(
        string='Horas SLA por defecto',
        default=0,
        help='Si es 0, se usa el SLA según prioridad del ticket.',
    )
    ticket_count = fields.Integer(
        string='Tickets',
        compute='_compute_ticket_count',
    )

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            [('category_id', 'in', self.ids)],
            groupby=['category_id'],
            aggregates=['__count'],
        )
        mapped = {cat.id: count for cat, count in ticket_data}
        for cat in self:
            cat.ticket_count = mapped.get(cat.id, 0)
