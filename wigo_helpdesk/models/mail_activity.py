# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import api, fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    is_helpdesk_postventa_activity = fields.Boolean(
        string='Es actividad postventa Helpdesk',
        compute='_compute_is_helpdesk_postventa_activity',
        store=False,
    )
    helpdesk_postventa_call_date = fields.Datetime(
        string='Fecha de llamada',
        default=lambda self: fields.Datetime.now(),
    )
    helpdesk_postventa_done_by = fields.Many2one(
        'res.users',
        string='Realizada por',
        default=lambda self: self.env.user,
    )
    helpdesk_postventa_state = fields.Selection(
        [('pending', 'Pendiente'), ('done', 'Realizada')],
        string='Estado postventa',
        default='pending',
        required=True,
    )
    helpdesk_postventa_satisfaction = fields.Selection(
        [
            ('1', 'Muy insatisfecho'),
            ('2', 'Insatisfecho'),
            ('3', 'Neutral'),
            ('4', 'Satisfecho'),
            ('5', 'Muy satisfecho'),
        ],
        string='Nivel de satisfaccion',
    )
    helpdesk_postventa_comment = fields.Text(
        string='Comentarios del cliente',
    )

    @api.depends('res_model', 'activity_type_id')
    def _compute_is_helpdesk_postventa_activity(self):
        activity_type_model = self.env['mail.activity.type']
        postventa_type = activity_type_model.search([
            ('name', '=', 'Postventa Helpdesk')
        ], limit=1)
        postventa_type_id = postventa_type.id

        for activity in self:
            activity.is_helpdesk_postventa_activity = bool(
                activity.res_model == 'helpdesk.ticket'
                and postventa_type_id
                and activity.activity_type_id.id == postventa_type_id
            )

    def _helpdesk_postventa_summary_html(self):
        self.ensure_one()
        satisfaction_labels = dict(self._fields['helpdesk_postventa_satisfaction'].selection)
        state_labels = dict(self._fields['helpdesk_postventa_state'].selection)

        satisfaction_text = satisfaction_labels.get(self.helpdesk_postventa_satisfaction, '-')
        state_text = state_labels.get(self.helpdesk_postventa_state, '-')
        call_date = fields.Datetime.to_string(self.helpdesk_postventa_call_date) if self.helpdesk_postventa_call_date else '-'
        done_by = self.helpdesk_postventa_done_by.name or '-'
        comment = self.helpdesk_postventa_comment or '-'

        return Markup(
            '<b>Seguimiento Postventa (Actividad)</b><br/>'
            f'Fecha de llamada: {call_date}<br/>'
            f'Realizada por: {done_by}<br/>'
            f'Estado: {state_text}<br/>'
            f'Nivel de satisfaccion: {satisfaction_text}<br/>'
            f'Comentarios: {comment}'
        )

    def action_done(self):
        postventa_activities = self.filtered('is_helpdesk_postventa_activity')
        for activity in postventa_activities:
            if not activity.helpdesk_postventa_call_date:
                activity.helpdesk_postventa_call_date = fields.Datetime.now()
            if not activity.helpdesk_postventa_done_by:
                activity.helpdesk_postventa_done_by = self.env.user
            activity.helpdesk_postventa_state = 'done'

        regular_activities = self - postventa_activities
        res = super(MailActivity, regular_activities).action_done() if regular_activities else False

        for activity in postventa_activities:
            if activity.res_model != 'helpdesk.ticket' or not activity.res_id:
                continue
            ticket = self.env['helpdesk.ticket'].browse(activity.res_id)
            if not ticket.exists():
                continue

            vals = {
                'postventa_done': True,
                'postventa_date': fields.Date.to_date(activity.helpdesk_postventa_call_date) if activity.helpdesk_postventa_call_date else fields.Date.today(),
                'postventa_user_id': activity.helpdesk_postventa_done_by.id or self.env.user.id,
                'postventa_activity_id': activity.id,
            }
            if activity.helpdesk_postventa_satisfaction:
                vals['satisfaction'] = activity.helpdesk_postventa_satisfaction
            if activity.helpdesk_postventa_comment:
                vals['postventa_notes'] = activity.helpdesk_postventa_comment

            ticket.write(vals)
            ticket.message_post(body=activity._helpdesk_postventa_summary_html())

        if postventa_activities:
            return {'type': 'ir.actions.act_window_close'}
        return res
