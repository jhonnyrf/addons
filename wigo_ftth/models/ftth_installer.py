# -*- coding: utf-8 -*-
from odoo import models, fields


class FtthInstaller(models.Model):
    """Técnico o empresa instaladora externa (ej: Vladimir Terceros)."""
    _name = 'wigo.ftth.installer'
    _description = 'Técnico / Empresa Instaladora'
    _order = 'name'

    name = fields.Char(string='Nombre / Razón social', required=True)
    tipo = fields.Selection([
        ('person',  'Persona / Instalador individual'),
        ('company', 'Empresa subcontratista'),
    ], string='Tipo', default='person', required=True)
    encargado = fields.Char(string='Encargado responsable', help='Para empresas: nombre del responsable')
    phone = fields.Char(string='Teléfono / WhatsApp')
    state = fields.Selection([
        ('active',   'Activo'),
        ('inactive', 'Inactivo'),
    ], string='Estado', default='active')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notas')

    work_order_ids = fields.One2many('wigo.ftth.work.order', 'installer_id', string='Órdenes asignadas')
    work_order_count = fields.Integer(compute='_compute_wo_count', string='OTs')

    def _compute_wo_count(self):
        for r in self:
            r.work_order_count = len(r.work_order_ids)
