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

    prefix = fields.Char(string="Prefijo" , trim=False, default="gpon-olt_")
    use_chassis = fields.Boolean(string='Usar chasis', default=True)
    use_slot = fields.Boolean(string='Usar slot', default=True)

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
        domain = [
            ('olt_id', '=', olt_id),
            ('prefix', '=', self.prefix),
        ]
        if self.use_chassis:
            domain.append(('chassis', '=', self.chassis))
        if self.use_slot:
            domain.append(('slot', '=', self.slot))

        ports = self.env['wigo.ftth.olt.port'].search(domain)

        numbers = {
            int(p.port_number)
            for p in ports
            if p.port_number
        }

        return (max(numbers) if numbers else 0) + 1

    def _build_ports_values(self, olt_id, start_number):
        values = []

        for port_number in range(start_number, start_number + self.quantity):
            vals = {
                'olt_id': olt_id,
                'chassis': self.chassis,
                'slot': self.slot,
                'port_number': port_number,
                'prefix': self.prefix,
                'technology_id': self.technology_id.id,
                'use_chassis': self.use_chassis,
                'use_slot': self.use_slot,
                'use_port_number': True,
            }

            interface = self.env['wigo.ftth.olt.port']._build_interface_port_from_vals(vals)
            vals['interface_port'] = interface
            values.append(vals)

        return values

    def _build_interface(self, port_number):
        vals = {
            'prefix': self.prefix,
            'chassis': self.chassis,
            'slot': self.slot,
            'port_number': port_number,
            'use_chassis': self.use_chassis,
            'use_slot': self.use_slot,
            'use_port_number': True,
        }
        return self.env['wigo.ftth.olt.port']._build_interface_port_from_vals(vals)