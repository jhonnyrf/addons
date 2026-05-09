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
        string='Fecha programada',
        default=lambda self: fields.Datetime.now(),
    )
    helpdesk_postventa_state = fields.Selection(
        [('pending', 'Pendiente'), ('done', 'Realizada'), ('cancelled', 'Cancelada')],
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
        comment = self.helpdesk_postventa_comment or '-'

        return Markup(
            '<b>Seguimiento Postventa (Actividad)</b><br/>'
            f'Fecha programada: {call_date}<br/>'
            f'Estado: {state_text}<br/>'
            f'Nivel de satisfaccion: {satisfaction_text}<br/>'
            f'Comentarios: {comment}'
        )

    @api.model_create_multi
    def create(self, vals_list):
        activities = super().create(vals_list)
        for activity in activities:
            if activity.is_helpdesk_postventa_activity and activity.res_model == 'helpdesk.ticket':
                # Sincronizar creando un registro pendiente
                self.env['helpdesk.postventa.call'].create({
                    'ticket_id': activity.res_id,
                    'state': 'pending',
                    'call_date': activity.helpdesk_postventa_call_date or fields.Datetime.now(),
                    'deadline_date': activity.date_deadline,
                    'user_id': activity.user_id.id,
                    'activity_id': activity.id,
                })
        return activities

    def write(self, vals):
        res = super().write(vals)
        for activity in self.filtered(lambda a: a.res_model == 'helpdesk.ticket'):
            if activity.is_helpdesk_postventa_activity:
                call = self.env['helpdesk.postventa.call'].search([('activity_id', '=', activity.id)], limit=1)
                if call:
                    update_vals = {}
                    if 'helpdesk_postventa_call_date' in vals:
                        update_vals['call_date'] = activity.helpdesk_postventa_call_date
                    if 'date_deadline' in vals:
                        update_vals['deadline_date'] = activity.date_deadline
                    if 'user_id' in vals:
                        update_vals['user_id'] = activity.user_id.id
                    if 'helpdesk_postventa_state' in vals:
                        update_vals['state'] = activity.helpdesk_postventa_state
                    if 'helpdesk_postventa_satisfaction' in vals:
                        update_vals['satisfaction'] = activity.helpdesk_postventa_satisfaction
                    if 'helpdesk_postventa_comment' in vals:
                        update_vals['comment'] = activity.helpdesk_postventa_comment
                    if update_vals:
                        call.write(update_vals)
        return res
    def _action_done(self, feedback=False, attachment_ids=None):
        postventa_activities = self.filtered('is_helpdesk_postventa_activity')
        
        # Primero actualizamos nuestra tabla persistente
        for activity in postventa_activities:
            if activity.res_model != 'helpdesk.ticket' or not activity.res_id:
                continue
                
            call = self.env['helpdesk.postventa.call'].search([('activity_id', '=', activity.id)], limit=1)
            if not call:
                call = self.env['helpdesk.postventa.call'].create({
                    'ticket_id': activity.res_id,
                    'activity_id': activity.id,
                })
                
            call.write({
                'state': 'done' if activity.helpdesk_postventa_state != 'cancelled' else 'cancelled',
                'call_date': activity.helpdesk_postventa_call_date or fields.Datetime.now(),
                'user_id': activity.user_id.id,
                'satisfaction': activity.helpdesk_postventa_satisfaction,
                'comment': activity.helpdesk_postventa_comment,
            })
            
            ticket = self.env['helpdesk.ticket'].browse(activity.res_id)
            if ticket.exists():
                ticket.message_post(body=activity._helpdesk_postventa_summary_html())

        # Manejar Visitas
        visit_activities = self.filtered(lambda a: a.res_model == 'helpdesk.ticket' and a.summary == 'Visita tecnica programada')
        for activity in visit_activities:
            visit = self.env['helpdesk.visit'].search([('activity_id', '=', activity.id)], limit=1)
            if visit and visit.state not in ('done', 'cancelled'):
                visit.write({'state': 'done'})

        res = super(MailActivity, self)._action_done(feedback=feedback, attachment_ids=attachment_ids)
        return res

    def unlink(self):
        visit_activities = self.filtered(lambda a: a.res_model == 'helpdesk.ticket' and a.summary == 'Visita tecnica programada')
        for activity in visit_activities:
            visit = self.env['helpdesk.visit'].search([('activity_id', '=', activity.id)], limit=1)
            if visit and visit.state not in ('done', 'cancelled'):
                visit.write({'state': 'cancelled'})
        
        postventa_activities = self.filtered('is_helpdesk_postventa_activity')
        for activity in postventa_activities:
            call = self.env['helpdesk.postventa.call'].search([('activity_id', '=', activity.id)], limit=1)
            if call and call.state not in ('done', 'cancelled'):
                call.write({'state': 'cancelled'})
                
        return super().unlink()
