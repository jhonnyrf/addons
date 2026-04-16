# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class GenerateBoxesWizard(models.TransientModel):
    _name = 'generate.boxes.wizard'
    _description = 'Generar Cajas (NAPs)'

    # =========================
    # Fields
    # =========================

    quantity = fields.Integer(
        string='Cantidad',
        default=1,
        required=True,
    )

    port_capacity = fields.Selection(
        selection=[('8', '8 puertos'), ('16', '16 puertos')],
        string='Capacidad',
        default='16',
        required=True,
    )

    # =========================
    # Public Methods
    # =========================

    def action_generate(self):
        self.ensure_one()

        group = self._get_active_group()
        self._validate_capacity(group)

        box_values = self._build_box_values(group)
        boxes = self.env['wigo.ftth.box'].create(box_values)

        # Generate ports for each created box (delegated to model action).
        boxes.action_generate_ports()

        return {'type': 'ir.actions.act_window_close'}

    # =========================
    # Private Methods
    # =========================

    def _get_active_group(self):
        group_id = self.env.context.get('active_id')
        if not group_id:
            raise UserError('No se encontró el Grupo de Cajas activo.')

        group = self.env['wigo.ftth.box.group'].browse(group_id)
        if not group.exists():
            raise UserError('No se encontró el Grupo de Cajas activo.')

        return group

    def _validate_capacity(self, group):
        if self.quantity <= 0:
            raise UserError('La cantidad debe ser mayor a 0.')

        if not group.olt_port_id:
            raise UserError('Debe asignar un Puerto OLT al grupo antes de generar cajas.')

        current_used_ports = self._get_current_used_ports(group)
        requested_ports = int(self.port_capacity) * self.quantity
        total_ports_after_creation = current_used_ports + requested_ports

        splitter_capacity = self._get_splitter_capacity(group)
        pon_capacity = int(group.olt_port_id.capacity_max or 0)

        if pon_capacity <= 0:
            raise UserError('El Puerto OLT no tiene una capacidad máxima válida (capacity_max).')

        effective_capacity = min(pon_capacity, splitter_capacity)

        if total_ports_after_creation > effective_capacity:
            raise UserError(
                'No se pueden generar las cajas porque se excede la capacidad del grupo.\n\n'
                f'- Puertos actuales en el grupo: {current_used_ports}\n'
                f'- Puertos solicitados: {requested_ports}\n'
                f'- Total después de crear: {total_ports_after_creation}\n\n'
                f'- Límite por PON (capacity_max): {pon_capacity}\n'
                f'- Límite por Splitters (Nivel1 x Nivel2): {splitter_capacity}\n'
                f'- Límite efectivo: {effective_capacity}'
            )

        free_subinterfaces = int(group.olt_port_id.free_subinterfaces or 0)
        if requested_ports > free_subinterfaces:
            raise UserError(
                'No se pueden generar las cajas porque no hay suficientes subinterfaces libres.\n\n'
                f'- Subinterfaces libres: {free_subinterfaces}\n'
                f'- Puertos solicitados: {requested_ports}'
            )

    def _get_splitter_capacity(self, group):
        level_1_outputs = self._splitter_to_outputs(group.splitter_level_1, 'Splitter 1er nivel')
        level_2_outputs = self._splitter_to_outputs(group.splitter_level_2, 'Splitter 2do nivel')
        return level_1_outputs * level_2_outputs

    def _get_current_used_ports(self, group):
        capacities = group.box_ids.mapped('port_capacity')
        return sum(int(value) for value in capacities if value and str(value).isdigit())

    def _build_box_values(self, group):
        return [
            {
                'box_group_id': group.id,
                'port_capacity': self.port_capacity,
            }
            for _i in range(self.quantity)
        ]

    @staticmethod
    def _splitter_to_outputs(value, field_label):
        if not value:
            raise UserError(f'Debe configurar {field_label} antes de generar cajas.')

        # Expected values like: "1:8", "1:16", etc.
        parts = str(value).split(':', 1)
        outputs = parts[1] if len(parts) == 2 else ''

        if not outputs.isdigit() or int(outputs) <= 0:
            raise UserError(f'Valor inválido en {field_label}: {value}')

        return int(outputs)
