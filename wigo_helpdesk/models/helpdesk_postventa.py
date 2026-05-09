# -*- coding: utf-8 -*-
from odoo import api, fields, models

class HelpdeskPostventaCall(models.Model):
    _name = 'helpdesk.postventa.call'
    _description = 'Llamada de Seguimiento Postventa'
    _order = 'call_date desc, id desc'

    ticket_id = fields.Many2one(
        'helpdesk.ticket', 
        string='Ticket', 
        ondelete='cascade', 
        required=True
    )
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('done', 'Realizada'),
        ('cancelled', 'Cancelada')
    ], string='Estado', default='pending', required=True)
    call_date = fields.Datetime('Fecha programada')
    deadline_date = fields.Date('Fecha límite')
    user_id = fields.Many2one('res.users', string='Asignado a')
    satisfaction = fields.Selection([
        ('1', 'Muy insatisfecho'),
        ('2', 'Insatisfecho'),
        ('3', 'Neutral'),
        ('4', 'Satisfecho'),
        ('5', 'Muy satisfecho'),
    ], string='Nivel de satisfacción')
    comment = fields.Text('Comentarios del cliente')
    activity_id = fields.Many2one('mail.activity', string='Actividad vinculada', ondelete='set null')

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'
            if not rec.call_date:
                rec.call_date = fields.Datetime.now()
