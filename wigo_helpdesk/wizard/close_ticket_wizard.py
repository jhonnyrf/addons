# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HelpdeskCloseWizard(models.TransientModel):
    _name = 'helpdesk.close.wizard'
    _description = 'Cerrar Ticket / Registrar Postventa'

    ticket_id = fields.Many2one(
        comodel_name='helpdesk.ticket',
        string='Ticket',
        required=True,
    )
    resolution_notes = fields.Html(
        string='Notas de resolución',
        help='Describe cómo se resolvió el problema.',
    )
    postventa_done = fields.Boolean(
        string='Llamada postventa realizada',
        default=False,
    )
    postventa_date = fields.Date(
        string='Fecha de llamada',
        default=fields.Date.today,
    )
    satisfaction = fields.Selection(
        selection=[
            ('1', '⭐ Muy insatisfecho'),
            ('2', '⭐⭐ Insatisfecho'),
            ('3', '⭐⭐⭐ Neutral'),
            ('4', '⭐⭐⭐⭐ Satisfecho'),
            ('5', '⭐⭐⭐⭐⭐ Muy satisfecho'),
        ],
        string='Nivel de Satisfacción',
    )
    postventa_notes = fields.Text(
        string='Observaciones',
    )
    close_ticket = fields.Boolean(
        string='Cerrar el ticket',
        default=True,
    )

    def action_confirm(self):
        vals = {}
        if self.resolution_notes:
            vals['resolution_notes'] = self.resolution_notes
        if self.postventa_done:
            vals['postventa_done'] = True
            vals['postventa_date'] = self.postventa_date
            vals['postventa_user_id'] = self.env.uid
        if self.satisfaction:
            vals['satisfaction'] = self.satisfaction
        if self.postventa_notes:
            vals['postventa_notes'] = self.postventa_notes
        self.ticket_id.write(vals)
        if self.close_ticket:
            self.ticket_id.action_close()
        # Log en chatter
        body_parts = []
        if self.resolution_notes:
            body_parts.append(f'<b>Resolución:</b> {self.resolution_notes}')
        if self.postventa_done and self.satisfaction:
            body_parts.append(
                f'<b>Satisfacción del cliente:</b> {dict(self._fields["satisfaction"].selection).get(self.satisfaction)}'
            )
        if body_parts:
            self.ticket_id.message_post(
                body='<br/>'.join(body_parts),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        return {'type': 'ir.actions.act_window_close'}
