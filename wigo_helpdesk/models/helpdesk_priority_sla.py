# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HelpdeskPrioritySla(models.Model):
    _name = 'helpdesk.priority.sla'
    _description = 'Prioridad SLA'
    _order = 'sequence, id'

    config_id = fields.Many2one(
        comodel_name='helpdesk.sla.config',
        string='Configuración SLA',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Orden', default=10)
    name = fields.Char(string='Prioridad', required=True, translate=False)
    color = fields.Char(
        string='Color',
        default='#6c757d',
        help='Color hexadecimal. Ej: #dc3545',
    )
    hours_limit = fields.Float(string='Horas límite', default=24.0)
    attention_time = fields.Char(string='Tiempo de atención')
    active = fields.Boolean(default=True)
