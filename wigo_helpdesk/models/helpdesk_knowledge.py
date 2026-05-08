# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HelpdeskKnowledge(models.Model):
    _name = 'helpdesk.knowledge'
    _description = 'Base de Conocimiento Helpdesk'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(
        string='Título del Artículo',
        required=True,
        translate=True,
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    ticket_type_id = fields.Many2one(
        comodel_name='helpdesk.ticket.type',
        string='Tipo de Ticket',
        index=True,
    )
    area_id = fields.Many2one(
        comodel_name='hr.department',
        string='Departamento',
        index=True,
        help='Selecciona el departamento/área responsable de este artículo',
    )
    incident_type_ids = fields.Many2many(
        comodel_name='helpdesk.incident.type',
        relation='helpdesk_knowledge_incident_type_rel',
        column1='knowledge_id',
        column2='incident_type_id',
        string='Síntomas/Incidencias relacionados',
        help='Selecciona los síntomas/incidencias que este artículo ayuda a resolver.',
        domain="[('ticket_type_id', '=', ticket_type_id)]",
    )
    content = fields.Html(
        string='Contenido',
        required=True,
        sanitize=True,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )
    author_id = fields.Many2one(
        comodel_name='res.users',
        string='Autor',
        default=lambda self: self.env.uid,
    )

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    @api.onchange('ticket_type_id')
    def _onchange_ticket_type_id(self):
        if self.ticket_type_id:
            self.incident_type_ids = False
