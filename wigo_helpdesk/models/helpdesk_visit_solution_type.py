# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskVisitSolutionType(models.Model):
    _name = 'helpdesk.visit.solution.type'
    _description = 'Solucion de Visita Tecnica'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True, translate=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
