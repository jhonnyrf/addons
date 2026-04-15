from odoo import models, fields

class GenericConfirmWizard(models.TransientModel):
    _name = 'wigo.generic.confirm.wizard'
    _description = 'Wizard genérico de confirmación'

    message = fields.Text(string="Mensaje")
    model_name = fields.Char(string="Modelo")
    method_name = fields.Char(string="Método")
    res_id = fields.Integer(string="ID del registro")

    def action_confirm(self):
        self.ensure_one()

        record = self.env[self.model_name].browse(self.res_id)

        # Ejecutar método dinámicamente
        getattr(record, self.method_name)()

        return {'type': 'ir.actions.act_window_close'}