# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FtthClientServiceExt(models.Model):
    _inherit = 'wigo.ftth.client.service'

    helpdesk_ticket_ids = fields.One2many(
        'helpdesk.ticket',
        compute='_compute_helpdesk_ticket_ids',
        string='Incidencias de Helpdesk',
        readonly=True,
    )

    @api.depends()
    def _compute_helpdesk_ticket_ids(self):
        mapped = {}
        if self.ids:
            tickets = self.env['helpdesk.ticket'].search(
                [('ftth_service_id', 'in', self.ids)]
            )
            for ticket in tickets:
                service_id = ticket.ftth_service_id.id
                mapped.setdefault(service_id, self.env['helpdesk.ticket'])
                mapped[service_id] += ticket

        for record in self:
            record.helpdesk_ticket_ids = mapped.get(
                record.id, self.env['helpdesk.ticket']
            )
