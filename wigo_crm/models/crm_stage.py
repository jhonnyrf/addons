# -*- coding: utf-8 -*-
from odoo import models, fields


class CrmStage(models.Model):
    _inherit = 'crm.stage'
    _description = 'CRM Stage con configuración de botones'

    # Configuración de visibilidad de botones en kanban
    show_button_won = fields.Boolean(
        string='Mostrar botón "Ganado"',
        default=False,
        help='Mostrar botón Ganado en esta etapa del kanban'
    )
    
    show_button_lost = fields.Boolean(
        string='Mostrar botón "Perdido"',
        default=False,
        help='Mostrar botón Perdido en esta etapa del kanban'
    )
    
    show_button_new_contract = fields.Boolean(
        string='Mostrar botón "Nuevo Contrato"',
        default=False,
        help='Mostrar botón Nuevo Contrato en esta etapa del kanban'
    )
