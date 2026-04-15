# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HelpdeskAssignWizard(models.TransientModel):
    _name = 'helpdesk.assign.wizard'
    _description = 'Asignar / Escalar Ticket'

    ticket_id = fields.Many2one(
        comodel_name='helpdesk.ticket',
        string='Ticket',
        required=True,
    )
    area_id = fields.Many2one(
        comodel_name='hr.department',
        string='Área',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Asignado a',
        domain="[('department_id', 'child_of', area_id)]",
    )
    escalation_reason = fields.Text(
        string='Motivo del escalamiento',
    )
    note = fields.Text(
        string='Nota interna',
        help='Se agregará como mensaje interno al chatter del ticket.',
    )

    def action_assign(self):
        vals = {}
        if self.area_id:
            vals['area_id'] = self.area_id.id
        if self.employee_id:
            vals['employee_id'] = self.employee_id.id
            if self.employee_id.department_id and 'area_id' not in vals:
                vals['area_id'] = self.employee_id.department_id.id
            if self.employee_id.user_id:
                vals['user_id'] = self.employee_id.user_id.id
        # Si viene en modo escalamiento
        if self.env.context.get('escalate_mode'):
            vals['is_escalated'] = True
            if self.employee_id and self.employee_id.user_id:
                vals['escalated_to_id'] = self.employee_id.user_id.id
            if self.escalation_reason:
                vals['escalation_reason'] = self.escalation_reason
        self.ticket_id.write(vals)
        if self.note:
            self.ticket_id.message_post(
                body=self.note,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return {'type': 'ir.actions.act_window_close'}
