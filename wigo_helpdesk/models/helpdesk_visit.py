# -*- coding: utf-8 -*-
from odoo import api, fields, models

class HelpdeskVisit(models.Model):
    _name = 'helpdesk.visit'
    _description = 'Historial de Visitas Técnicas'
    _order = 'visit_date desc, id desc'

    ticket_id = fields.Many2one(
        'helpdesk.ticket', 
        string='Ticket', 
        ondelete='cascade', 
        required=True
    )
    technician_id = fields.Many2one(
        'hr.employee', 
        string='Técnico asignado', 
        required=True
    )
    visit_date = fields.Datetime(
        string='Fecha programada',
        default=fields.Datetime.now
    )
    deadline_date = fields.Date(
        string='Fecha límite'
    )
    activity_id = fields.Many2one(
        'mail.activity',
        string='Actividad vinculada',
        ondelete='set null'
    )
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En progreso'),
        ('done', 'Realizada'),
        ('rescheduled', 'Reagendada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado de visita', default='pending', required=True)
    notes = fields.Text('Notas de la visita')

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'

    def action_mark_rescheduled(self):
        for rec in self:
            rec.state = 'rescheduled'

    def action_mark_cancelled(self):
        for rec in self:
            rec.state = 'cancelled'
