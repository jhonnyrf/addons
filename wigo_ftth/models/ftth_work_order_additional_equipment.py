# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FtthWorkOrderAdditionalEquipment(models.Model):
    _name = 'wigo.ftth.work.order.additional.equipment'
    _description = 'Línea de equipo adicional en OT FTTH'
    _order = 'id desc'

    work_order_id = fields.Many2one(
        'wigo.ftth.work.order',
        string='Orden de trabajo',
        required=True,
        ondelete='cascade',
        index=True,
    )

    additional_equipment_id = fields.Many2one(
        'wigo.ftth.additional.equipment',
        string='Equipo adicional',
        required=True,
        ondelete='restrict',
        index=True,
    )

    marca = fields.Char(related='additional_equipment_id.marca', string='Marca', readonly=True)
    rotulo = fields.Char(related='additional_equipment_id.rotulo', string='Rótulo / Etiqueta', readonly=True)
    serial_number = fields.Char(related='additional_equipment_id.serial_number', string='S/N', readonly=True)
    state = fields.Selection(related='additional_equipment_id.state', string='Estado', readonly=True)
    notes = fields.Html(related='additional_equipment_id.notes', string='Notas', readonly=True)

    _sql_constraints = [
        (
            'unique_equipment_per_work_order',
            'unique(work_order_id, additional_equipment_id)',
            'El equipo adicional ya está agregado en esta orden de trabajo.',
        ),
    ]

    @api.constrains('work_order_id', 'additional_equipment_id')
    def _check_deactivation_work_order(self):
        for record in self:
            if record.work_order_id.work_type == 'deactivation':
                raise ValidationError('No se pueden agregar equipos adicionales en órdenes de trabajo de baja.')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            equipment = record.additional_equipment_id.sudo()
            if equipment.work_order_id != record.work_order_id:
                equipment.write({'work_order_id': record.work_order_id.id})
        return records

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            equipment = record.additional_equipment_id.sudo()
            if equipment.work_order_id != record.work_order_id:
                equipment.write({'work_order_id': record.work_order_id.id})
        return res

    def unlink(self):
        equipment_by_line = {line.id: line.additional_equipment_id for line in self}
        work_order_by_line = {line.id: line.work_order_id for line in self}
        res = super().unlink()

        for line_id, equipment in equipment_by_line.items():
            work_order = work_order_by_line.get(line_id)
            if not equipment or not work_order:
                continue

            still_linked = self.search_count([
                ('additional_equipment_id', '=', equipment.id),
                ('work_order_id', '=', work_order.id),
            ])
            if still_linked:
                continue

            if equipment.work_order_id == work_order and not equipment.client_service_id:
                equipment.sudo().write({'work_order_id': False})

        return res
