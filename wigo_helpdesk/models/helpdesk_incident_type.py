# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re


class HelpdeskIncidentType(models.Model):
    _name = 'helpdesk.incident.type'
    _description = 'Tipo de Incidencia'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', readonly=True, help='Se genera automáticamente')
    sequence = fields.Integer(string='Secuencia', default=10)
    
    area_id = fields.Many2one(
        comodel_name='hr.department',
        string='Área',
        required=False,
        help='Selecciona el área (departamento) responsable de este tipo de incidencia',
    )
    
    ticket_type_id = fields.Many2one(
        comodel_name='helpdesk.ticket.type',
        string='Tipo de Ticket',
        required=True,
        default=lambda self: self.env['helpdesk.ticket.type'].search([], order='sequence', limit=1),
        help='Define para qué tipo de ticket estará disponible este síntoma.',
    )
    
    priority_suggestion = fields.Many2one(
        comodel_name='helpdesk.priority.sla',
        string='Prioridad',
        help='Prioridad sugerida para este tipo de incidencia',
        ondelete='set null',
    )
    
    color = fields.Char(
        string='Color',
        related='priority_suggestion.color',
        store=True,
    )
    
    active = fields.Boolean(string='Activo', default=True)
    ticket_count = fields.Integer(string='Tickets', compute='_compute_ticket_count')

    @api.onchange('name')
    def _onchange_name(self):
        """Generar automáticamente el código a partir del nombre"""
        if self.name:
            code = self.name.lower()
            code = re.sub(r'[^a-z0-9_]', '', code.replace(' ', '_'))
            self.code = code

    def _compute_ticket_count(self):
        data = self.env['helpdesk.ticket']._read_group(
            [('incident_type_id', 'in', self.ids)],
            groupby=['incident_type_id'],
            aggregates=['__count'],
        )
        mapped = {t.id: c for t, c in data}
        for rec in self:
            rec.ticket_count = mapped.get(rec.id, 0)
