# -*- coding: utf-8 -*-
from odoo import models, fields


class CancelWorkOrderWizard(models.TransientModel):
    _name = 'wigo.ftth.cancel.work.order.wizard'
    _description = 'Asistente para cancelar Orden de Trabajo'

    work_order_id = fields.Many2one(
        'wigo.ftth.work.order',
        string='Orden de Trabajo',
        required=True,
        readonly=True,
    )
    cancellation_reason = fields.Text(
        string='Motivo de cancelación',
        required=True,
    )

    def action_confirm_cancel(self):
        self.ensure_one()
        wo = self.work_order_id
        wo.write({'cancellation_reason': self.cancellation_reason})
        wo.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
