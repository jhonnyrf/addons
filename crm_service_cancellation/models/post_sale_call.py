# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmPostSaleCall(models.Model):
    _name = 'crm.post.sale.call'
    _description = 'Llamada de seguimiento posventa'
    _order = 'post_sale_call_date desc, id desc'

    activity_id = fields.Many2one('mail.activity', string='Actividad origen', ondelete='set null')
    lead_id = fields.Many2one('crm.lead', string='Oportunidad/Cliente', ondelete='set null')
    post_sale_client_id = fields.Many2one('res.partner', string='Cliente', required=True)
    post_sale_cf_code = fields.Char(string='Codigo CF')
    post_sale_call_date = fields.Datetime(string='Fecha de programación', required=True)
    date_deadline = fields.Date(string='Fecha límite')
    post_sale_done_by = fields.Many2one('res.users', string='Realizada por', required=True)
    post_sale_satisfaction = fields.Selection(
        [
            ('satisfied', 'Satisfecho'),
            ('partial', 'Parcialmente satisfecho'),
            ('unsatisfied', 'Insatisfecho'),
        ],
        string='Nivel de satisfaccion',
    )
    post_sale_customer_comment = fields.Html(string='Comentarios del cliente')
    post_sale_state = fields.Selection(
        [('pending', 'Pendiente'), ('done', 'Realizada'), ('cancelled', 'Cancelada')],
        string='Estado posventa',
        default='pending',
        required=True,
    )
