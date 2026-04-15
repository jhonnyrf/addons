# -*- coding: utf-8 -*-
from odoo import models, fields


class InternetPlanSettings(models.Model):
    _name = 'internet.plan.settings'
    _description = 'Configuración de Planes de Internet'

    name_installation_cost = fields.Char(
        string="Nombre del costo de instalación",
        required=True,
    )
    installation_cost = fields.Float(
        string="Costo de instalación (Bs)",
        required=True,
    )
    active = fields.Boolean(string="Activo", default=True, required=True)
    description = fields.Text(string="Descripción")

    def action_save_installation_cost(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'Costo de instalación guardado correctamente.',
                'type': 'success',
                'sticky': False,
            },
        }
