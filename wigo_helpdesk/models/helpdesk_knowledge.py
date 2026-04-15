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
    category_id = fields.Many2one(
        comodel_name='helpdesk.category',
        string='Categoría',
        index=True,
    )
    area = fields.Selection(
        selection=[
            ('technical', 'Área Técnica'),
            ('commercial', 'Área Comercial'),
            ('both', 'Ambas Áreas'),
        ],
        string='Área',
        default='technical',
    )
    # Tipos de incidencia que resuelve este artículo
    incident_type_ids = fields.Many2many(
        comodel_name='helpdesk.incident.type',
        relation='helpdesk_knowledge_incident_type_rel',
        column1='knowledge_id',
        column2='incident_type_id',
        string='Tipos de incidencia relacionados',
        help='Selecciona los síntomas/incidencias que este artículo ayuda a resolver.',
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
    views = fields.Integer(
        string='Vistas',
        default=0,
        readonly=True,
    )
    tag_ids = fields.Many2many(
        comodel_name='helpdesk.tag',
        relation='helpdesk_knowledge_tag_rel',
        column1='knowledge_id',
        column2='tag_id',
        string='Etiquetas',
    )
    author_id = fields.Many2one(
        comodel_name='res.users',
        string='Autor',
        default=lambda self: self.env.uid,
    )

    def action_increment_view(self):
        self.sudo().write({'views': self.views + 1})

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
