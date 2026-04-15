# -*- coding: utf-8 -*-
from odoo import models, fields


class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Área de Helpdesk'
    _order = 'name'

    name = fields.Char(
        string='Nombre del Área',
        required=True,
        translate=True,
    )
    description = fields.Text(
        string='Descripción',
    )
    member_ids = fields.Many2many(
        comodel_name='res.users',
        relation='helpdesk_team_users_rel',
        column1='team_id',
        column2='user_id',
        string='Miembros',
        domain="[('share', '=', False)]",
    )
    team_leader_id = fields.Many2one(
        comodel_name='res.users',
        string='Líder del Área',
        domain="[('share', '=', False)]",
    )
    team_email = fields.Char(
        string='Email del Área',
    )
    team_phone = fields.Char(
        string='Teléfono / WhatsApp',
    )
    area = fields.Selection(
        selection=[
            ('technical', 'Área Técnica'),
            ('commercial', 'Área Comercial'),
            ('support', 'Soporte General'),
        ],
        string='Área',
        default='support',
        required=True,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    ticket_count = fields.Integer(
        string='Tickets Abiertos',
        compute='_compute_ticket_count',
    )

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            [('team_id', 'in', self.ids), ('stage_id.is_close', '=', False)],
            groupby=['team_id'],
            aggregates=['__count'],
        )
        mapped = {team.id: count for team, count in ticket_data}
        for team in self:
            team.ticket_count = mapped.get(team.id, 0)

    def action_open_tickets(self):
        self.ensure_one()
        return {
            'name': f'Tickets - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,kanban,form',
            'domain': [('team_id', '=', self.id), ('is_closed', '=', False)],
        }
