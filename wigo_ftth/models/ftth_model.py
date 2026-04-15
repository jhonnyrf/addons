# -*- coding: utf-8 -*-
from odoo import models, fields


class FtthModel(models.Model):
    _name = 'wigo.ftth.model'
    _description = 'Modelo FTTH'
    _order = 'name'

    name = fields.Char(string='Modelo', required=True)
    active = fields.Boolean(string='Activo', default=True)
    notes = fields.Text(string='Notas')
