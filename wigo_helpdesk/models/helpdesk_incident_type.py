# -*- coding: utf-8 -*-
from odoo import models, fields, api
import re


class HelpdeskIncidentType(models.Model):
    _name = 'helpdesk.incident.type'
    _description = 'Tipo de Incidencia'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True, translate=True)
    code = fields.Char(string='Código', readonly=True, help='Se genera automáticamente')
    sequence = fields.Integer(string='Secuencia', default=10)
    
    area_id = fields.Many2one(
        comodel_name='hr.department',
        string='Área',
        required=True,
        help='Selecciona el área (departamento) responsable de este tipo de incidencia',
    )
    
    ticket_type_id = fields.Many2one(
        comodel_name='helpdesk.ticket.type',
        string='Tipo de Ticket',
        required=True,
        default=lambda self: self.env['helpdesk.ticket.type'].search([], order='sequence', limit=1),
        help='Define para qué tipo de ticket estará disponible este síntoma.',
    )
    
    priority_suggestion = fields.Selection(
        selection=[
            ('0', 'Baja'),
            ('1', 'Media'),
            ('2', 'Alta'),
            ('3', 'Crítica'),
        ],
        string='Prioridad sugerida',
        default='1',
        required=True,
    )
    
    # Color automático según la prioridad
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=True,
        help='Se asigna automáticamente según la prioridad',
    )
    
    active = fields.Boolean(string='Activo', default=True)
    ticket_count = fields.Integer(string='Tickets', compute='_compute_ticket_count')

    # Mapeo de colores por prioridad
    PRIORITY_COLORS = {
        '0': 9,  # Verde (Baja)
        '1': 3,  # Azul (Media)
        '2': 6,  # Naranja (Alta)
        '3': 1,  # Rojo (Crítica)
    }

    @api.depends('priority_suggestion')
    def _compute_color(self):
        """Asignar color automáticamente según la prioridad"""
        for rec in self:
            rec.color = self.PRIORITY_COLORS.get(rec.priority_suggestion, 0)

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
