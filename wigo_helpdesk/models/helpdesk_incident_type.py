# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskIncidentType(models.Model):
    _name = 'helpdesk.incident.type'
    _description = 'Tipo de Incidencia'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True, translate=True)
    code = fields.Char(string='Código', size=20)
    sequence = fields.Integer(string='Secuencia', default=10)
    area = fields.Selection(
        selection=[
            ('technical', 'Técnica'),
            ('commercial', 'Comercial'),
            ('accounting', 'Contabilidad'),
            ('both', 'Ambas'),
        ],
        string='Área', default='technical', required=True,
    )
    ticket_type_scope = fields.Selection(
        selection=[
            ('incident', 'Reclamo / Incidente'),
            ('request', 'Solicitud'),
            ('both', 'Ambos'),
        ],
        string='Tipo de Ticket',
        default='incident',
        required=True,
        help='Define para qué tipo de ticket estará disponible este síntoma.',
    )
    requires_visit = fields.Boolean(
        string='Requiere visita técnica',
        default=False,
        help='Al seleccionar este tipo, se marcará visita requerida automáticamente.',
    )
    priority_suggestion = fields.Selection(
        selection=[('0', 'Baja'), ('1', 'Media'), ('2', 'Alta'), ('3', 'Crítica')],
        string='Prioridad sugerida',
        default='1',
    )
    color = fields.Integer(string='Color', default=0)
    active = fields.Boolean(string='Activo', default=True)
    ticket_count = fields.Integer(string='Tickets', compute='_compute_ticket_count')

    def _compute_ticket_count(self):
        data = self.env['helpdesk.ticket']._read_group(
            [('incident_type_id', 'in', self.ids)],
            groupby=['incident_type_id'],
            aggregates=['__count'],
        )
        mapped = {t.id: c for t, c in data}
        for rec in self:
            rec.ticket_count = mapped.get(rec.id, 0)
