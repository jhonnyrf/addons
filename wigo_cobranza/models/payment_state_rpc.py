# -*- coding: utf-8 -*-

from odoo import api, models


class WigoPagoEstadoRPC(models.Model):
    _inherit = 'wigo.pago.estado'

    @api.model
    def register_contable_justification_for_client(self, pago_id, justification):
        """Called from client: register the provided justification on the pago.

        This delegates to the existing `_register_contable_justification`
        server method so all server-side auditing and chatter posting
        remains in one place.
        """
        pago = self.browse(pago_id)
        if not pago:
            return False
        pago._register_contable_justification(justification)
        return True
