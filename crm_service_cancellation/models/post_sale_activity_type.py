# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmPostSaleActivityType(models.Model):
    _name = 'crm.post.sale.activity.type'
    _description = 'Tipo de actividad de posventa CRM'

    activity_type_id = fields.Many2one(
        'mail.activity.type',
        string='Tipo de actividad',
        required=True,
        ondelete='cascade',
        index=True,
    )
