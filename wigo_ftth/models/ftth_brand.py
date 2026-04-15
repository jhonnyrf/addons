# -*- coding: utf-8 -*-
from odoo import models, fields


class FtthBrand(models.Model):
    _name = 'wigo.ftth.brand'
    _description = 'Marca FTTH'
    _order = 'name'

    name = fields.Char(string='Marca', required=True)
    active = fields.Boolean(string='Activo', default=True)
    notes = fields.Text(string='Notas')
