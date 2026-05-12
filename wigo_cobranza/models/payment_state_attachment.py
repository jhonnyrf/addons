from odoo import models, fields, api
from odoo.exceptions import UserError


class WigoPagoEstadoAttachmentViewerWizard(models.TransientModel):
    _name = 'wigo.pago.estado.attachment.viewer.wizard'
    _description = 'Payment Attachment Viewer Wizard'

    pago_id = fields.Many2one(
        'wigo.pago.estado',
        string='Registro de Pago',
        required=True, readonly=True,
    )
    action_type = fields.Selection([
        ('view', 'Ver en grande'),
        ('download', 'Descargar'),
    ], string='Acción', required=True, default='view', readonly=True)
    available_attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_available_attachment_ids',
        string='Adjuntos disponibles',
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo',
        required=True,
        domain="[('id', 'in', available_attachment_ids)]",
    )

    @api.depends('pago_id')
    def _compute_available_attachment_ids(self):
        for rec in self:
            rec.available_attachment_ids = rec.pago_id._get_all_comprobante_attachments()
            if not rec.attachment_id and rec.available_attachment_ids:
                rec.attachment_id = rec.available_attachment_ids.sorted('id', reverse=True)[0]

    def action_confirm(self):
        self.ensure_one()
        if not self.attachment_id:
            raise UserError('Debes seleccionar un archivo.')

        return {
            'type': 'ir.actions.act_url',
            'url': (
                f"/web/content?model=ir.attachment&id={self.attachment_id.id}"
                f"&field=datas&filename_field=name"
                f"&download={'true' if self.action_type == 'download' else 'false'}"
            ),
            'target': 'self' if self.action_type == 'download' else 'new',
        }
