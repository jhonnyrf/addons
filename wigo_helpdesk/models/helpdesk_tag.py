# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskTag(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Etiqueta del Ticket'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
