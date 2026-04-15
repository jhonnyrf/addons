# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class GeneratePortsWizard(models.TransientModel):
    _name = 'wigo.ftth.generate.ports.wizard'
    _description = 'Generar Puertos OLT'

    # =========================
    # Fields
    # =========================
    technology_id = fields.Many2one(
        'wigo.ftth.technology',
        string="Tecnología",
        required=True
    )

    prefix = fields.Char(string="Prefijo")
    chassis = fields.Integer(default=1)
    slot = fields.Integer(default=1)
    quantity = fields.Integer(string="Cantidad", default=16)

    # =========================
    # Public Methods
    # =========================
    def action_generate(self):
        self.ensure_one()

        olt = self._get_active_olt()

        self._validate_inputs()

        start_number = self._get_start_port_number(olt.id)

        values_list = self._build_ports_values(olt.id, start_number)

        self.env['wigo.ftth.olt.port'].create(values_list)

    # =========================
    # Private Methods
    # =========================
    def _get_active_olt(self):
        olt_id = self.env.context.get('active_id')
        if not olt_id:
            raise UserError("No se encontró la OLT activa.")

        return self.env['wigo.ftth.olt'].browse(olt_id)

    def _validate_inputs(self):
        if not self.technology_id:
            raise UserError("Debe seleccionar una tecnología")

        if not self.prefix:
            raise UserError("Debe ingresar el prefijo")

        if self.quantity <= 0:
            raise UserError("La cantidad debe ser mayor a 0")

    def _get_start_port_number(self, olt_id):
        ports = self.env['wigo.ftth.olt.port'].search([            
            ('olt_id', '=', olt_id),
            ('prefix', '=', self.prefix),
            ('chassis', '=', self.chassis),
            ('slot', '=', self.slot),
        ])

        numbers = {
            int(p.port_number)
            for p in ports
            if p.port_number
        }

        return (max(numbers) if numbers else 0) + 1

    def _build_ports_values(self, olt_id, start_number):
        values = []

        for port_number in range(start_number, start_number + self.quantity):
            values.append({
                'olt_id': olt_id,
                'interface_port': self._build_interface(port_number),
                'chassis': self.chassis,
                'slot': self.slot,
                'port_number': port_number,
                'prefix': self.prefix,
                'technology_id': self.technology_id.id,
            })

        return values

    def _build_interface(self, port_number):
        return f"{self.prefix}_{self.chassis}/{self.slot}/{port_number}"