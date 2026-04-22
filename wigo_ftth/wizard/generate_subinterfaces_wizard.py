# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class GenerateSubinterfacesWizard(models.TransientModel):
    _name = 'wigo.ftth.generate.subinterfaces.wizard'
    _description = 'Generar Subinterfaces OLT'

    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto PON',
        required=True,
        readonly=True,
        ondelete='cascade',
    )

    capacity_max = fields.Integer(
        string='Capacidad máx. del puerto',
        related='olt_port_id.capacity_max',
        readonly=True,
    )

    existing_count = fields.Integer(
        string='Subinterfaces existentes',
        compute='_compute_existing_count',
        readonly=True,
    )

    # Total number of subinterfaces desired for the port after generation.
    target_capacity = fields.Integer(
        string='Generar hasta',
        required=True,
        help='Cantidad total de subinterfaces que debe tener el puerto luego de generar (no excede la capacidad máxima).'
    )

    vlan_id = fields.Integer(
        string='VLAN',
        required=True,
        default=1,
        help='VLAN que se asignará a las subinterfaces creadas (rango: 1-4094).'
    )

    prefix = fields.Char(
        string='Prefijo',
        required=True,
        default='gpon-olt',
        help='Prefijo para el nombre de subinterfaz. Ej: gpon-olt'
    )

    # UI helper: keep a plain string representation (no thousands separators like 4.000).
    vlan_text = fields.Char(
        string='VLAN',
        compute='_compute_vlan_text',
        inverse='_inverse_vlan_text',
        store=False,
        help='VLAN sin separadores de miles (ej: 4000).'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        port_id = self.env.context.get('default_olt_port_id') or self.env.context.get('active_id')
        if port_id and 'olt_port_id' in fields_list and not res.get('olt_port_id'):
            res['olt_port_id'] = port_id

        if port_id and 'target_capacity' in fields_list and not res.get('target_capacity'):
            port = self.env['wigo.ftth.olt.port'].browse(port_id)
            if port.exists():
                res['target_capacity'] = port.capacity_max
                if 'prefix' in fields_list and not res.get('prefix'):
                    res['prefix'] = port.prefix or 'gpon-olt'

        res.setdefault('vlan_id', 1)
        res.setdefault('prefix', 'gpon-olt')
        return res

    @api.depends('olt_port_id')
    def _compute_existing_count(self):
        for wizard in self:
            wizard.existing_count = len(wizard.olt_port_id.subinterface_ids) if wizard.olt_port_id else 0

    @api.depends('vlan_id')
    def _compute_vlan_text(self):
        for wizard in self:
            wizard.vlan_text = str(wizard.vlan_id) if wizard.vlan_id else ''

    def _inverse_vlan_text(self):
        for wizard in self:
            raw = (wizard.vlan_text or '').strip()
            if not raw:
                wizard.vlan_id = False
                continue

            normalized = raw.replace('.', '').replace(',', '').replace(' ', '')
            if not normalized.isdigit():
                raise ValidationError('La VLAN debe ser un número entero (1-4094).')

            wizard.vlan_id = int(normalized)

    @api.constrains('vlan_id')
    def _check_vlan_id_range(self):
        for wizard in self:
            if wizard.vlan_id is None:
                raise ValidationError('La VLAN es obligatoria.')
            if wizard.vlan_id < 1 or wizard.vlan_id > 4094:
                raise ValidationError('La VLAN debe estar entre 1 y 4094.')

    @api.constrains('target_capacity')
    def _check_target_capacity(self):
        for wizard in self:
            if wizard.target_capacity is None:
                raise ValidationError('Debe indicar la capacidad a generar.')
            if wizard.target_capacity <= 0:
                raise ValidationError('La capacidad a generar debe ser mayor a 0.')

            if wizard.olt_port_id and wizard.target_capacity > wizard.olt_port_id.capacity_max:
                raise ValidationError(
                    'La capacidad a generar no puede exceder la capacidad máxima del puerto.'
                )

    def action_generate(self):
        self.ensure_one()

        if not self.olt_port_id:
            raise UserError('No se encontró el puerto PON activo.')

        port = self.olt_port_id
        max_cap = port.capacity_max

        if self.target_capacity > max_cap:
            raise UserError(
                f"La capacidad a generar ({self.target_capacity}) no puede exceder la capacidad máxima del puerto ({max_cap})."
            )

        existing = set(port.subinterface_ids.mapped('subinterface_number'))
        existing_count = len(existing)

        if self.target_capacity < existing_count:
            raise UserError(
                f"El puerto ya tiene {existing_count} subinterfaces. 'Generar hasta' no puede ser menor a ese valor."
            )

        vals_list = []
        for num in range(1, self.target_capacity + 1):
            if num not in existing:
                vals_list.append({
                    'olt_port_id': port.id,
                    'subinterface_number': num,
                    'vlan_id': self.vlan_id,
                    'prefix': self.prefix or 'gpon-olt',
                })

        if vals_list:
            self.env['wigo.ftth.subinterface'].create(vals_list)

        return {'type': 'ir.actions.act_window_close'}
