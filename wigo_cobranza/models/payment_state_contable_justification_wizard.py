# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WigoPagoEstadoContableJustificationWizard(models.TransientModel):
    _name = 'wigo.pago.estado.contable.justification.wizard'
    _description = 'Payment Contable Justification Wizard'

    pago_id = fields.Many2one(
        'wigo.pago.estado',
        string='Pago',
        required=True,
        readonly=True,
    )
    justification = fields.Text(
        string='Justificación',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not res.get('pago_id') and self.env.context.get('default_pago_id'):
            res['pago_id'] = self.env.context['default_pago_id']
        return res

    def action_confirm(self):
        self.ensure_one()
        self.pago_id._register_contable_justification(self.justification)
        return {
            'type': 'ir.actions.act_window_close',
            'infos': {'justification_confirmed': True},
        }