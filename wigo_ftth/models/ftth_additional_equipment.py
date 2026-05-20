# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FtthAdditionalEquipment(models.Model):
    _name = 'wigo.ftth.additional.equipment'
    _description = 'Equipo adicional FTTH'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Equipo adicional', required=True)
    marca = fields.Char(string='Marca')
    rotulo = fields.Char(string='Rótulo / Etiqueta')
    serial_number = fields.Char(string='S/N')
    work_order_id = fields.Many2one('wigo.ftth.work.order', string='OT asignada')
    client_service_id = fields.Many2one('wigo.ftth.client.service', string='Servicio asignado')
    state = fields.Selection([
        ('available', 'Disponible'),
        ('assigned', 'Asignado'),
    ], string='Estado', default='available', required=True, tracking=True)
    notes = fields.Html(string='Notas')

    @api.onchange('client_service_id', 'work_order_id')
    def _onchange_assignment_links(self):
        for record in self:
            if record.client_service_id or record.work_order_id:
                record.state = 'assigned'
            else:
                record.state = 'available'

    @api.model_create_multi
    def create(self, vals_list):
        # Mantener consistencia: si hay OT o servicio asignado => state='assigned', si no => 'available'.
        normalized = []
        for vals in vals_list:
            v = dict(vals)
            v['state'] = 'assigned' if (v.get('client_service_id') or v.get('work_order_id')) else 'available'
            normalized.append(v)
        return super().create(normalized)

    def write(self, vals):
        # En write, si se intenta setear state manualmente lo normalizamos según enlaces de asignación.
        vals_clean = dict(vals)
        if 'client_service_id' in vals_clean or 'work_order_id' in vals_clean:
            for rec in self:
                client_service_id = vals_clean.get('client_service_id', rec.client_service_id.id)
                work_order_id = vals_clean.get('work_order_id', rec.work_order_id.id)
                desired_state = 'assigned' if (client_service_id or work_order_id) else 'available'
                super(FtthAdditionalEquipment, rec).write(dict(vals_clean, state=desired_state))
            return True
        else:
            # Evitar desalineación (state siempre deriva de enlaces de asignación)
            vals_clean.pop('state', None)

        res = super().write(vals_clean)

        # Reforzar consistencia si se cambió desde otros flujos.
        if 'client_service_id' not in vals and 'work_order_id' not in vals:
            for rec in self:
                desired = 'assigned' if (rec.client_service_id or rec.work_order_id) else 'available'
                if rec.state != desired:
                    super(FtthAdditionalEquipment, rec).write({'state': desired})

        return res

    @api.constrains('state', 'client_service_id', 'work_order_id')
    def _check_assignment(self):
        for record in self:
            if record.state == 'assigned' and not (record.client_service_id or record.work_order_id):
                raise ValidationError('Un equipo asignado debe tener una OT o un servicio asociado.')
