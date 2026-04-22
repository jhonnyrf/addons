# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class FtthRegional(models.Model):
    _name = 'wigo.ftth.regional'
    _description = 'Regional FTTH'
    _order = 'name'

    # =========================
    # Fields
    # =========================
    name = fields.Char(
        string='Ciudad / Regional',
        required=True,
    )

    prefix = fields.Char(
        string='Prefijo',
        required=True,
    )

    active = fields.Boolean(
        string="Activo",
        default=True,
        required=True,
    )

    nodo_ids = fields.One2many(
        'wigo.ftth.nodo',
        'regional_id',
        string='Nodos',
    )

    nodo_count = fields.Integer(
        string='N° Nodos',
        compute='_compute_nodo_count',
    )

    notes = fields.Html(
        string='Notas',
    )

    # =========================
    # Constraints (SQL)
    # =========================
    _unique_name  = models.Constraint(
        'unique(name)',
        'No puedes crear la regional porque ya existe otra con el mismo nombre.'
    )
    _unique_prefix  = models.Constraint(
        'unique(prefix)',
        'No puedes crear la regional porque ya existe otra con el mismo prefijo.'
    )

    # =========================
    # Compute Methods
    # =========================
    @api.depends('nodo_ids')
    def _compute_nodo_count(self):
        for record in self:
            record.nodo_count = len(record.nodo_ids)
            

class FtthNode(models.Model):
    _name = 'wigo.ftth.nodo'
    _description = 'FTTH Aggregation Node'
    _rec_name = 'name'

    # =========================
    # Fields
    # =========================
    name = fields.Char(string='Nombre del Nodo', required=True)

    number = fields.Char(
        string='Nº Nodo',
        required=True
    )

    node_type = fields.Selection(
        [
            ('aggregation', 'Agregación'),
            ('acess', 'Acceso'),
        ],
        string='Tipo de Nodo',
        required=True
    )

    regional_id = fields.Many2one(
        'wigo.ftth.regional',
        string='Regional',
        required=True,
        ondelete='restrict'
    )

    address = fields.Char(string='Dirección física')

    coordinates = fields.Char(
        string='Coordenadas GPS',
        help='Format: latitude,longitude'
    )

    active = fields.Boolean(string="Activo", default=True, required=True)

    notes = fields.Html(string='Notas')

    olt_ids = fields.One2many(
        'wigo.ftth.olt',
        'node_id',
        string='OLTs'
    )

    olt_count = fields.Integer(
        compute='_compute_olt_count',
        string='OLT Count'
    )

    # =========================
    # SQL Constraints
    # =========================
    _unique_number_per_regional = models.Constraint(
        'unique(number, regional_id)',
        'El número de nodo ya existe en esta regional.'
    )

    # =========================
    # Create Override
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_number(vals.get('number'))

        return super().create(vals_list)

    # =========================
    # Constraints
    # =========================
    @api.constrains('number')
    def _check_number(self):
        for record in self:
            self._validate_number(record.number)

    # =========================
    # Compute Methods
    # =========================
    @api.depends('olt_ids')
    def _compute_olt_count(self):
        for record in self:
            record.olt_count = len(record.olt_ids)

    @api.depends('name', 'number')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name}-{record.number}"

    # =========================
    # Onchange
    # =========================
    @api.onchange('regional_id')
    def _onchange_regional_id(self):
        if self.regional_id:
            self.number = self._get_next_available_number(self.regional_id)

    # =========================
    # Default Values
    # =========================
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        regional_id = self.env.context.get('default_regional_id')
        
        if regional_id:
           regional = self.env['wigo.ftth.regional'].browse(regional_id)
           if regional.exists():
               number = self._get_next_available_number(regional)               
               res['number'] = number
               res['regional_id'] = regional_id
        return res

    # =========================
    # Private Methods
    # =========================
    def _validate_number(self, number):
        if not number:
            raise ValidationError("Se requiere el número de nodo.")

        if not str(number).isdigit():
            raise ValidationError("El número de nodo debe ser numérico.")

    def _get_next_available_number(self, regional):        
        real_regional_id = regional._origin.id if regional._origin else regional.id
        nodes = self.search(
            [('regional_id', '=', real_regional_id)],
            order='number asc'
        )

        used_numbers = {
            int(node.number)
            for node in nodes
            if node.number and node.number.isdigit()
        }

        i = 1
        while True:
            if i not in used_numbers:
                return str(i).zfill(2)
            i += 1

    def _get_next_global_number(self):
        last = self.search([], order='number desc', limit=1)

        if last and last.number and last.number.isdigit():
            next_number = int(last.number) + 1
        else:
            next_number = 1

        return str(next_number).zfill(2)

class FtthTechnology(models.Model):
    _name = 'wigo.ftth.technology'
    _description = 'Technology FTTH'
    _rec_name    = 'name'

    # =========================
    # Fields
    # =========================
    name = fields.Char(string='Nombre', required=True)  
    prefix = fields.Char(string='Prefijo', required=True)  
    notes = fields.Html(string='Notas')
    active = fields.Boolean(string="Activo", default=True, required=True)
    
    # =========================
    # SQL Constraints
    # =========================
    _name_technology_unique = models.Constraint(
        'unique(name)',
        'No puedes crear la tecnología porque ya existe otra con el mismo nombre.'
    )
    _prefix_technology_unique = models.Constraint(
        'unique(prefix)',
        'No puedes crear la tecnología porque ya existe otra con el mismo prefijo.'
    )

class FtthOlt(models.Model):
    _name = 'wigo.ftth.olt'
    _description = 'OLT — Optical Line Terminal'
    _rec_name = 'name'

    # =========================
    # Fields
    # =========================
    regional_prefix = fields.Char(
        string='Prefijo Regional',
        compute='_compute_regional_data',
        store=True
    )

    node_number = fields.Char(
        string='N° Nodo',
        compute='_compute_regional_data',
        store=True
    )

    olt_number = fields.Char(string='N° OLT')  

    technology_id = fields.Many2one(
        'wigo.ftth.technology',
        string='Tecnología',
        required=True
    )

    technology_prefix = fields.Char(
        string='Prefijo Tecnología',
        compute='_compute_technology_prefix',
        store=True
    )

    olt_code = fields.Char(
        string='Código OLT',
        compute='_compute_olt_code',
        store=True,
        index=True
    )

    name = fields.Char(string='Nombre descriptivo')
    brand = fields.Char(string='Marca')
    model = fields.Char(string='Modelo')

    node_id = fields.Many2one(
        'wigo.ftth.nodo',
        string='Nodo',
        required=True,
    )

    active = fields.Boolean(string="Activo", default=True, required=True)
    notes = fields.Html(string='Notas técnicas')

    port_ids = fields.One2many(
        'wigo.ftth.olt.port',
        'olt_id',
        string='Puertos PON'
    )
    odn_ids = fields.One2many(
        'wigo.ftth.odn',
        'olt_id',
        string='ODNs asociadas'
    )

    port_count = fields.Integer(
        compute='_compute_port_count',
        string='Puertos'
    )

    odn_id = fields.Many2one(
        'wigo.ftth.odn',
        string='ODN asociada',
        compute='_compute_odn',
        store=True
    )

    has_odn = fields.Boolean(
        string='Ya tiene ODN',
        compute='_compute_has_odn',
        store=True,
        help='Indica si la OLT ya tiene una ODN asociada (solo se permite una por OLT).'
    )

    # =========================
    # SQL Constraints
    # =========================
    _olt_number_node_unique = models.Constraint(
        'unique(olt_number, node_id)',
        'El N° OLT debe ser único por nodo.'
    )
    
    # =========================
    # Compute Methods
    # =========================
    @api.depends('node_id')
    def _compute_regional_data(self):
        for rec in self:
            node = rec.node_id
            rec.regional_prefix = node.regional_id.prefix if node else False
            rec.node_number = node.number if node else False



    @api.depends('technology_id')
    def _compute_technology_prefix(self):
        for rec in self:
            rec.technology_prefix = (
                rec.technology_id.prefix if rec.technology_id else False
            )

    @api.depends(
        'regional_prefix',
        'node_number',
        'olt_number',
        'technology_prefix'
    )
    def _compute_olt_code(self):
        for rec in self:
            parts = [
                rec.regional_prefix,
                rec.node_number,
                rec.olt_number,
                rec.technology_prefix
            ]
            rec.olt_code = "-".join(filter(None, parts))

    @api.depends('port_ids')
    def _compute_port_count(self):
        for rec in self:
            rec.port_count = len(rec.port_ids)

    @api.depends('port_ids')
    def _compute_odn(self):
        for rec in self:
            odn = self.env['wigo.ftth.odn'].search(
                [('olt_id', '=', rec.id)],
                limit=1
            )
            rec.odn_id = odn.id if odn else False

    @api.depends('odn_id')
    def _compute_has_odn(self):
        for rec in self:
            rec.has_odn = bool(rec.odn_id)

    @api.depends('name', 'olt_code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.olt_code or rec.name or f'OLT #{rec.id}'

    # =========================
    # ORM Overrides
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        self._assign_missing_olt_numbers(vals_list)
        return super().create(vals_list)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        node_id = res.get('node_id')
        if node_id:
            res['olt_number'] = self._get_next_available_olt_number(node_id)

        return res

    # =========================
    # Onchange
    # =========================
    @api.onchange('node_id')
    def _onchange_node_id(self):
        if self.node_id:
            self.olt_number = self._get_next_available_olt_number(self.node_id)

    # =========================
    # Actions
    # =========================
    def action_open_generate_ports_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar Puertos',
            'res_model': 'wigo.ftth.generate.ports.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }

    # =========================
    # Default Values
    # =========================
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        node_id = self.env.context.get('default_node_id')
        
        if node_id:
           node = self.env['wigo.ftth.nodo'].browse(node_id)
           if node.exists():
               number = self._get_next_available_olt_number(node)               
               res['number'] = number
               res['node_id'] = node_id
        return res
    # =========================
    # Private Methods
    # =========================    
    def _assign_missing_olt_numbers(self, vals_list):
        for vals in vals_list:
            if not vals.get('olt_number') and vals.get('node_id'):
                node = self.env['wigo.ftth.nodo'].browse(vals['node_id'])
                vals['olt_number'] = self._get_next_available_olt_number(node)

    def _get_next_available_olt_number(self, node):
        real_node_id = node._origin.id if node._origin else node.id
        
        olts = self.search(
            [('node_id', '=', real_node_id)],
            order='olt_number asc'
        )        
        used_numbers = {int(o.olt_number) for o in olts if o.olt_number and o.olt_number.isdigit()}
        i = 1
        while True:
            if i not in used_numbers:
                return str(i).zfill(2)
            i += 1

class FtthOltPort(models.Model):
    _name = 'wigo.ftth.olt.port'
    _description = 'Puerto PON de OLT'
    _rec_name = 'interface_port'

    # Estados considerados como ocupación real (asignación a cliente/proceso comercial)
    OCCUPIED_STATES = ('allocated', 'reserved', 'active')

    # =========================
    # Fields
    # =========================
    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT',
        required=True,
        ondelete='cascade',
        index=True
    )

    interface_port = fields.Char(
        string='Puerto físico',
        help='Ej: gpon-olt_1/1/1',
        index=True
    )

    port_number = fields.Integer(
        string='Nº Puerto',
        required=True,
        help='Número secuencial del puerto'
    )

    technology_id = fields.Many2one(
        'wigo.ftth.technology',
        string='Tecnología',
        required=True
    )

    capacity_max = fields.Integer(string='Capacidad máx.', default=128)
    chassis = fields.Integer(string="Chasis", default=1)
    slot = fields.Integer(string="Slot", default=1)

    active = fields.Boolean(string="Activo", default=True, required=True)

    prefix = fields.Char(
        default="gpon-olt",
        help='Prefijo tecnológico del puerto'
    )

    notes = fields.Html(string='Notas')

    subinterface_ids = fields.One2many(
        'wigo.ftth.subinterface',
        'olt_port_id',
        string='Subinterfaces'
    )

    used_subinterfaces = fields.Integer(
        compute='_compute_occupancy',
        store=True,
        string='Usadas'
    )

    free_subinterfaces = fields.Integer(
        compute='_compute_occupancy',
        store=True,
        string='Libres'
    )

    occupancy_percent = fields.Float(
        compute='_compute_occupancy',
        store=True,
        string='Ocupación %'
    )

    box_group_ids = fields.One2many(
        'wigo.ftth.box.group',
        'olt_port_id',
        string='Grupos de cajas'
    )

    # =========================
    # SQL Constraints
    # =========================   
    _puerto_chasis_slot_unique = models.Constraint(
        'unique(olt_id,prefix, chassis, slot, port_number)',
        'El puerto (Chasis, Slot, Número) debe ser único dentro de la OLT. '
        'Ya existe otro puerto con la misma configuración física.'
    )
    
    _puerto_interface_unique = models.Constraint(
        'unique(olt_id, interface_port)',
        'El nombre de interfaz debe ser único dentro de la OLT. '
        'Ya existe otro puerto con la misma interfaz física.'
    )

    # =========================
    # Constraints
    # =========================
    @api.constrains('port_number')
    def _check_port_number_positive(self):
        for rec in self:
            if rec.port_number and rec.port_number <= 0:
                raise ValidationError(
                    f"El número de puerto debe ser positivo. Recibido: {rec.port_number}"
                )

    @api.constrains('chassis', 'slot')
    def _check_chassis_slot_range(self):
        for rec in self:
            if rec.chassis and not 1 <= rec.chassis <= 16:
                raise ValidationError(f"Chasis inválido: {rec.chassis}. Debe estar entre 1 y 16.")
            if rec.slot and not 1 <= rec.slot <= 16:
                raise ValidationError(f"Slot inválido: {rec.slot}. Debe estar entre 1 y 16.")

    @api.constrains('subinterface_ids', 'capacity_max')
    def _check_capacity(self):
        for rec in self:
            occupied = len(rec.subinterface_ids.filtered(lambda s: s.state in self.OCCUPIED_STATES))
            if occupied > rec.capacity_max:
                raise ValidationError(
                    f"Capacidad excedida en puerto {rec.port_number} de {rec.olt_id.olt_code}\n\n"
                    f"Ocupadas: {occupied} | Máxima: {rec.capacity_max}\n(RN-01)"
                )

    # =========================
    # Compute
    # =========================
    @api.depends('subinterface_ids.state', 'capacity_max')
    def _compute_occupancy(self):
        for rec in self:
            used = len(rec.subinterface_ids.filtered(lambda s: s.state in self.OCCUPIED_STATES))
            rec.used_subinterfaces = used
            rec.free_subinterfaces = rec.capacity_max - used
            rec.occupancy_percent = (used / rec.capacity_max * 100) if rec.capacity_max else 0

    # =========================
    # Onchange
    # =========================
    @api.onchange('prefix', 'chassis', 'slot', 'port_number')
    def _onchange_interface_port(self):
        for rec in self:
            rec.interface_port = rec._build_interface_port()

    @api.onchange('olt_id')
    def _onchange_olt_id(self):
        if self.olt_id:
            self.port_number = self._get_next_available_port_number(self.olt_id.id)
            self.interface_port = self._build_interface_port()

    # =========================
    # ORM Overrides
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        self._prepare_create_vals(vals_list)
        return super().create(vals_list)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        olt_id = self.env.context.get('default_olt_id') or res.get('olt_id')
        if hasattr(olt_id, 'id'):
            olt_id = olt_id.id

        if olt_id:
            res['port_number'] = self._get_next_available_port_number(olt_id)

        res.setdefault('chassis', 1)
        res.setdefault('slot', 1)
        res.setdefault('prefix', 'gpon-olt')

        return res

    # =========================
    # Public Methods
    # =========================
    def name_get(self):
        return [
            (rec.id, f'{rec.olt_id.olt_code} / Puerto {rec.port_number}')
            for rec in self
        ]

    def action_open_generate_subinterfaces_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar Subinterfaces',
            'res_model': 'wigo.ftth.generate.subinterfaces.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_olt_port_id': self.id,
                'default_target_capacity': self.capacity_max,
                'default_vlan_id': 1,
                'default_prefix': self.prefix or 'gpon-olt',
            },
        }

    def action_generate_subinterfaces(self):
        # Backward compatible behavior: generate missing subinterfaces up to capacity_max.
        for port in self:
            existing = set(port.subinterface_ids.mapped('subinterface_number'))
            max_cap = port.capacity_max

            next_num = 1
            while len(existing) < max_cap:
                if next_num not in existing:
                    self.env['wigo.ftth.subinterface'].create({
                        'olt_port_id': port.id,
                        'subinterface_number': next_num,
                        'vlan_id': 1,
                        'prefix': port.prefix or 'gpon-olt',
                    })
                    existing.add(next_num)
                next_num += 1

    # =========================
    # Private Methods
    # =========================
    def _prepare_create_vals(self, vals_list):
        for vals in vals_list:
            olt_id = vals.get('olt_id')
            if not olt_id:
                continue

            if not vals.get('port_number'):
                vals['port_number'] = self._get_next_available_port_number(olt_id)

            vals['interface_port'] = self._build_interface_port_from_vals(vals)

    def _build_interface_port(self):
        if not (self.prefix and self.chassis and self.slot and self.port_number):
            return self.interface_port
        return f"{self.prefix}_{self.chassis}/{self.slot}/{self.port_number}"

    def _build_interface_port_from_vals(self, vals):
        prefix = vals.get('prefix', 'gpon-olt')
        chassis = vals.get('chassis', 1)
        slot = vals.get('slot', 1)
        port = vals.get('port_number')

        if not port:
            return vals.get('interface_port')

        return f"{prefix}_{chassis}/{slot}/{port}"

    @api.model
    def _get_next_available_port_number(self, olt_id):
        ports = self.search(
            [('olt_id', '=', olt_id), ('port_number', '!=', False)],
            order='port_number asc'
        )

        used = {p.port_number for p in ports if p.port_number}

        i = 1
        while i in used:
            i += 1
        return i

class FtthOdn(models.Model):
    _name = 'wigo.ftth.odn'
    _description = 'ODN — Red de Distribución Óptica'
    _rec_name = 'name'
    _order = 'olt_id, name'

    # =========================
    # Fields
    # =========================
    name = fields.Char(
        string='Nombre ODN',
        required=True,
        help='Ej: ODN_01, ODN_02'
    )
    
    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT asociada',
        domain=[('has_odn', '=', False)],
        required=True,
        ondelete='restrict'
    )
    regional_id = fields.Many2one(
        'wigo.ftth.regional',
        string='Regional',
        compute='_compute_regional_id',
        store=True,
        index=True,
        help='Regional asociada a la ODN (obtenida desde la OLT).'
    )
    node_name = fields.Char(
        string='Nombre del Nodo (desde OLT)',
        compute='_compute_node_name',
        store=True,
        help='Se obtiene automáticamente del nodo asociado a la OLT'
    )
    odn_number = fields.Char(string='N° ODN')

    odf_port = fields.Char(
        string='ODF / Puerto',
        help='Puerto del ODF donde sale la fibra. Ej: 01, 02'
    )

    notes = fields.Html(string='Notas')

    active = fields.Boolean(
        string="Activo",
        default=True,
        required=True
    )

    box_group_ids = fields.One2many(
        'wigo.ftth.box.group',
        'odn_id',
        string='Grupos de cajas'
    )

    # =========================
    # SQL Constraints
    # =========================

    _olt_unique = models.Constraint(
        'unique(olt_id)',
        'Esta OLT ya tiene una ODN asociada. Solo se permite una ODN por OLT.'
    )

    def init(self):
        """Limpia datos históricos para evitar fallos en actualización.

        - Elimina constraint SQL legado que puede romper la recomputación de `regional_id`.
        - Normaliza `odn_number` y resuelve duplicados por regional de forma determinística.
        """
        self.env.cr.execute(
            'ALTER TABLE wigo_ftth_odn '
            'DROP CONSTRAINT IF EXISTS wigo_ftth_odn_odn_number_regional_unique'
        )

        self.env.cr.execute(
            """
            SELECT
                o.id,
                r.id AS regional_id,
                o.odn_number
            FROM wigo_ftth_odn o
            LEFT JOIN wigo_ftth_olt olt ON olt.id = o.olt_id
            LEFT JOIN wigo_ftth_nodo n ON n.id = olt.node_id
            LEFT JOIN wigo_ftth_regional r ON r.id = n.regional_id
            ORDER BY r.id NULLS LAST, o.id
            """
        )
        rows = self.env.cr.fetchall()

        rows_by_regional = {}
        for odn_id, regional_id, odn_number in rows:
            rows_by_regional.setdefault(regional_id, []).append((odn_id, odn_number))

        updates = []
        for regional_id, regional_rows in rows_by_regional.items():
            if not regional_id:
                continue

            used_numbers = set()
            pending_ids = []

            for odn_id, odn_number in regional_rows:
                text = str(odn_number).strip() if odn_number not in (False, None) else ''
                normalized = None
                if text.isdigit():
                    value = int(text)
                    if value > 0:
                        normalized = str(value)

                if normalized and normalized not in used_numbers:
                    used_numbers.add(normalized)
                    if text != normalized:
                        updates.append((normalized, odn_id))
                else:
                    pending_ids.append(odn_id)

            i = 1
            for odn_id in pending_ids:
                while str(i) in used_numbers:
                    i += 1
                new_number = str(i)
                used_numbers.add(new_number)
                updates.append((new_number, odn_id))
                i += 1

        if updates:
            for new_number, odn_id in updates:
                self.env.cr.execute(
                    'UPDATE wigo_ftth_odn SET odn_number = %s WHERE id = %s',
                    (new_number, odn_id)
                )

    # =========================
    # Constraints
    # =========================

    @api.constrains('olt_id')
    def _check_unique_olt_id(self):
        for record in self:
            if not record.olt_id:
                continue

            duplicate = self.search([
                ('olt_id', '=', record.olt_id.id),
                ('id', '!=', record.id)
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    'Esta OLT ya tiene una ODN asociada. Solo se permite una ODN por OLT.'
                )

    @api.constrains('odf_port')
    def _check_number(self):
        for record in self:
            self._validate_number(record.odf_port)

    @api.constrains('odn_number', 'olt_id')
    def _check_odn_number_unique_by_regional(self):
        if self.env.context.get('install_mode'):
            return

        for record in self:
            if not record.odn_number or not record.regional_id:
                continue

            normalized = self._normalize_odn_number(record.odn_number)
            duplicates = self.search([
                ('id', '!=', record.id),
                ('regional_id', '=', record.regional_id.id),
                ('odn_number', '!=', False),
            ])
            if any(self._normalize_odn_number(dup.odn_number) == normalized for dup in duplicates):
                raise ValidationError(
                    'El N° ODN debe ser único dentro de la misma regional.'
                )

    # =========================
    # Display
    # =========================
    def name_get(self):
        return [
            (rec.id, f'{rec.name} ({rec.olt_id.codigo_olt})')
            for rec in self
        ]

    # =========================
    # ORM Overrides
    # =========================
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if 'odn_number' in fields_list and not res.get('odn_number'):
            regional_id = self._get_regional_id_from_vals(res)
            if regional_id:
                res['odn_number'] = self._get_next_odn_number(regional_id=regional_id)

        return res

    @api.model_create_multi
    def create(self, vals_list):
        next_number_by_regional = {}

        for vals in vals_list:
            _logger.info(f"Creando ODN con valores: {vals}")
            if vals.get('odn_number'):
                vals['odn_number'] = self._normalize_odn_number(vals['odn_number'])
                continue

            regional_id = self._get_regional_id_from_vals(vals)
            if not regional_id:
                continue

            if regional_id not in next_number_by_regional:
                next_number_by_regional[regional_id] = self._get_next_odn_number_int(regional_id)

            if not vals.get('odn_number'):
                vals['odn_number'] = self._format_number(next_number_by_regional[regional_id])
                next_number_by_regional[regional_id] += 1

        records = super().create(vals_list)

        for record in records:
            record._update_has_odn_on_olt()

        return records
    def write(self, vals):
        if vals.get('odn_number'):
            vals['odn_number'] = self._normalize_odn_number(vals['odn_number'])
        
        old_olts = self.mapped('olt_id')
        res = super().write(vals)        
        new_olts = self.mapped('olt_id')       
        olts_to_update = (old_olts | new_olts).filtered(lambda o: o)

        for olt in olts_to_update:
            has_odn = bool(self.search([
                ('olt_id', '=', olt.id)
            ], limit=1))

            _logger.info(
                f"Actualizando has_odn para OLT {olt.id} a {has_odn}"
            )

            olt.write({'has_odn': has_odn})

        return res    
   # ═════════════════════════════════════════════════════════════════════════════
    # Compute Methods
    # ═════════════════════════════════════════════════════════════════════════════

    @api.depends('olt_id', 'olt_id.node_id', 'olt_id.node_id.regional_id')
    def _compute_regional_id(self):
        for record in self:
            record.regional_id = record.olt_id.node_id.regional_id if record.olt_id else False

    @api.depends('olt_id')
    def _compute_node_name(self):
        for record in self:
            record.node_name = record.olt_id.node_id.display_name if record.olt_id else False

    # ═════════════════════════════════════════════════════════════════════════════
    # Onchange
    # ═════════════════════════════════════════════════════════════════════════════

    @api.onchange('olt_id')
    def _onchange_olt_id(self):
        if self.olt_id:
            if not self.odn_number:
                self.odn_number = self._get_next_odn_number(regional_id=self.olt_id.node_id.regional_id.id)
            if not self.name:
                self.name = self._build_odn_name(self.odn_number)
    # =========================
    # Private Methods
    # =========================    
    def _validate_number(self, number):
        if not number:
            raise ValidationError("Se requiere el puerto de odf.")

        if not str(number).isdigit():
            raise ValidationError("El puerto de odf debe ser numérico.")
    def _build_odn_name(self, odn_number=None):
        if not odn_number:
            return "ODN_X"
        return f"ODN_{odn_number}"  
    def unlink(self):
        olts = self.mapped('olt_id')

        res = super().unlink()

        for olt in olts:
            has_odn = bool(self.search([
                ('olt_id', '=', olt.id)
            ], limit=1))

            olt.has_odn = has_odn

        return res
    def _update_has_odn_on_olt(self):
        olts = self.mapped('olt_id')

        for olt in olts:
            if olt:
                has_odn = bool(self.search([
                    ('olt_id', '=', olt.id)
                ], limit=1))

                _logger.info(
                    f"Actualizando has_odn para OLT {olt.id} a {has_odn}"
                )

                olt.has_odn = has_odn
         
            
                
    def _get_next_odn_number(self, regional_id=None):
        next_number = self._get_next_odn_number_int(regional_id)
        return self._format_number(next_number)

    def _get_next_odn_number_int(self, regional_id=None):
        domain = [('odn_number', '!=', False)]
        if regional_id:
            domain.append(('olt_id.node_id.regional_id', '=', regional_id))

        odns = self.search(domain)

        numbers = {
            int(str(o.odn_number))
            for o in odns
            if o.odn_number and str(o.odn_number).isdigit()
        }

        return (max(numbers) if numbers else 0) + 1

    @api.model
    def _get_regional_id_from_vals(self, vals):
        olt_id = vals.get('olt_id') or self.env.context.get('default_olt_id')
        if not olt_id:
            return False

        olt = self.env['wigo.ftth.olt'].browse(olt_id)
        return olt.node_id.regional_id.id if olt and olt.node_id and olt.node_id.regional_id else False

    @api.model
    def _normalize_odn_number(self, number):
        text = str(number).strip() if number not in (False, None) else ''
        if not text:
            return False
        if not text.isdigit():
            raise ValidationError('El N° ODN debe ser numérico.')
        return str(int(text))

    @staticmethod
    def _format_number(number):
        return str(int(number))

class FtthBoxGroup(models.Model):
    _name = 'wigo.ftth.box.group'
    _description = 'Grupo de Cajas / Splitters'
    _rec_name = 'group_number'
    _order = 'zone_id, olt_port_id, group_number'

    # ═════════════════════════════════════════════════════════════════════════════
    # Fields
    # ═════════════════════════════════════════════════════════════════════════════

    group_number = fields.Char(
        string='Nº Grupo',
        required=True,
        help='Número único del grupo (ej: 01, 02, 03). Solo números.'
    )

    zone_id = fields.Many2one(
        'wigo.zone',
        string='Zona',
        required=True,
        ondelete='restrict',
        help='Zona geográfica a la que pertenece este grupo de cajas'
    )

    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto OLT',
        required=True,
        ondelete='restrict'
    )

    odn_id = fields.Many2one(
        'wigo.ftth.odn',
        string='ODN',
        ondelete='restrict'
    )

    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT (desde ODN)',
        compute='_compute_olt_id',
        store=True,
        help='Se obtiene automáticamente de la ODN seleccionada'
    )

    splitter_level_1 = fields.Selection(
        selection=[
            ('1:2', '1:2'), ('1:4', '1:4'), ('1:8', '1:8'),
            ('1:16', '1:16'), ('1:32', '1:32'), ('1:64', '1:64'),
        ],
        string='Splitter 1er nivel',
        help='Divisor óptico entre la OLT y las cajas NAP'
    )

    splitter_level_2 = fields.Selection(
        selection=[
            ('1:2', '1:2'), ('1:4', '1:4'), ('1:8', '1:8'),
            ('1:16', '1:16'), ('1:32', '1:32'),
        ],
        string='Splitter 2do nivel',
        help='Divisor óptico dentro de la caja NAP hacia el cliente'
    )

    active = fields.Boolean(string="Activo", default=True, required=True)
    notes = fields.Html(string='Notas')

    box_ids = fields.One2many(
        'wigo.ftth.box',
        'box_group_id',
        string='Cajas'
    )

    box_count = fields.Integer(
        compute='_compute_box_count',
        string='N° Cajas'
    )

    total_ports = fields.Integer(
        compute='_compute_total_ports',
        store=True,
        string='Total puertos'
    )

    # ═════════════════════════════════════════════════════════════════════════════
    # SQL Constraints
    # ═════════════════════════════════════════════════════════════════════════════

    _group_number_unique = models.Constraint(
        'unique(odn_id,group_number)',
        'El número de grupo debe ser único en el sistema.'
    )

    # ═════════════════════════════════════════════════════════════════════════════
    # Validations
    # ═════════════════════════════════════════════════════════════════════════════

    @api.constrains('group_number')
    def _check_group_number_is_numeric(self):
        for record in self:
            if not record.group_number.isdigit():
                raise ValidationError(
                    "El número de grupo debe contener solo dígitos (0-9). "
                    f"Valor ingresado: '{record.group_number}'"
                )

    # ═════════════════════════════════════════════════════════════════════════════
    # Defaults
    # ═════════════════════════════════════════════════════════════════════════════

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        self._prefill_from_context(values)
        values['group_number'] = self._get_next_group_number(values.get('odn_id'))

        return values

    def _get_next_group_number(self, odn_id=None):
       
        if not odn_id:
            groups = self.search([('group_number', '!=', False)])
        else:
         
            groups = self.search([
                ('group_number', '!=', False),
                ('odn_id', '=', odn_id)
            ])

        numbers = [
            int(g.group_number)
            for g in groups
            if g.group_number.isdigit()
        ]

      
        if not numbers:
            return '01'

        max_number = max(numbers)
        return str(max_number + 1).zfill(2)

    def _prefill_from_context(self, values):
        olt_port_id = self.env.context.get('default_olt_port_id') or values.get('olt_port_id')

        if not olt_port_id:
            return

        values['olt_port_id'] = olt_port_id
        olt_port = self.env['wigo.ftth.olt.port'].browse(olt_port_id)

        if olt_port.olt_id:
            odn = self.env['wigo.ftth.odn'].search(
                [('olt_id', '=', olt_port.olt_id.id)],
                limit=1
            )
            if odn:
                values['odn_id'] = odn.id
                
           
            values['olt_id'] = olt_port.olt_id.id

    # ═════════════════════════════════════════════════════════════════════════════
    # Compute Methods
    # ═════════════════════════════════════════════════════════════════════════════

    @api.depends('odn_id')
    def _compute_olt_id(self):
        for record in self:
            record.olt_id = record.odn_id.olt_id if record.odn_id else False

    @api.depends('box_ids')
    def _compute_box_count(self):
        for record in self:
            record.box_count = len(record.box_ids)

    @api.depends('box_ids.port_capacity')
    def _compute_total_ports(self):
        for record in self:
            record.total_ports = sum(
                int(box.port_capacity) for box in record.box_ids
            )

    # ═════════════════════════════════════════════════════════════════════════════
    # Onchange
    # ═════════════════════════════════════════════════════════════════════════════

    @api.onchange('odn_id')
    def _onchange_odn_id(self):
        if not self.odn_id:
            self.olt_port_id = False
            return

        if self.olt_port_id and self.olt_port_id.olt_id != self.odn_id.olt_id:
            self.olt_port_id = False

   
        if self.odn_id:
            self.group_number = self._get_next_group_number(self.odn_id.id)

    @api.onchange('olt_port_id')
    def _onchange_olt_port_id(self):
      
        if not self.olt_port_id:
            return

      
        if self.olt_port_id.olt_id:
            odn = self.env['wigo.ftth.odn'].search(
                [('olt_id', '=', self.olt_port_id.olt_id.id)],
                limit=1
            )
            if odn:
                self.group_number = self._get_next_group_number(odn.id)

    # ═════════════════════════════════════════════════════════════════════════════
    # Constraints
    # ═════════════════════════════════════════════════════════════════════════════

    @api.constrains('box_ids')
    def _check_total_ports(self):
        for record in self:
            total = sum(int(box.port_capacity) for box in record.box_ids)

            if total > 128:
                zone_name = record.zone_id.name if record.zone_id else 'sin zona'
                raise ValidationError(
                    f"El Grupo {record.group_number} ({zone_name}) suma {total} puertos, "
                    f"que supera el máximo de 128 por grupo (RN-06)."
                )

    # ═════════════════════════════════════════════════════════════════════════════
    # Actions
    # ═════════════════════════════════════════════════════════════════════════════

    def action_open_generate_boxes_wizard(self):
        self.ensure_one()

        default_capacity = '16'
        if self.splitter_level_2 and ':' in self.splitter_level_2:
            try:
                _left, right = self.splitter_level_2.split(':', 1)
                if right in ('8', '16'):
                    default_capacity = right
            except Exception:
                pass

        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar Cajas NAP',
            'res_model': 'generate.boxes.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_port_capacity': default_capacity,
                'default_quantity': 1,
            },
        }

    # ═════════════════════════════════════════════════════════════════════════════
    # Display
    # ═════════════════════════════════════════════════════════════════════════════

    def name_get(self):
        result = []
        for record in self:
            zone = f' — {record.zone_id.name}' if record.zone_id else ''
            result.append((record.id, f'Grupo {record.group_number}{zone}'))
        return result


class FtthBox(models.Model):    
    _name = 'wigo.ftth.box'
    _description = 'Caja / Splitter FTTH'
    _rec_name = 'identifier'
    _order = 'box_group_id, identifier'

    # ═════════════════════════════════════════════════════════════════════════════
    # Constants
    # ═════════════════════════════════════════════════════════════════════════════
    PORT_CAPACITY_CHOICES = [
        ('8', '8 puertos'),
        ('16', '16 puertos'),
    ]
    FIRST_LETTER = 'A'
    STATE_FREE = 'free'
    NON_OCCUPIED_PORT_STATES = ('free', 'occupied')

    # ═════════════════════════════════════════════════════════════════════════════
    # Fields
    # ═════════════════════════════════════════════════════════════════════════════
    identifier = fields.Char(
        string='Identificador NAP',
        required=True,
        help='Ej: 01A, 01B, 02A'
    )

    box_group_id = fields.Many2one(
        'wigo.ftth.box.group',
        string='Grupo',
        required=True,
        ondelete='cascade'
    )

    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT',
        related='box_group_id.olt_id',
        store=True,
        readonly=True,
    )

    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto OLT',
        related='box_group_id.olt_port_id',
        store=True,
        readonly=True,
    )

    port_capacity = fields.Selection(
        selection=PORT_CAPACITY_CHOICES,
        string='Capacidad',
        required=True,
        default='16'
    )

    physical_location = fields.Char(string='Ubicación física')
    gps_coordinates = fields.Char(string='Coordenadas GPS')
    active = fields.Boolean(string="Activo", default=True, required=True)
    notes = fields.Html(string='Notas')

    port_ids = fields.One2many(
        'wigo.ftth.box.port',
        'box_id',
        string='Puertos'
    )

    free_ports = fields.Integer(
        compute='_compute_free_ports',
        string='Libres'
    )

    # ═════════════════════════════════════════════════════════════════════════════
    # Computed Fields
    # ═════════════════════════════════════════════════════════════════════════════
    @api.depends('port_ids', 'port_ids.state')
    def _compute_free_ports(self):      
        for record in self:
            record.free_ports = len(
                record.port_ids.filtered(lambda port: port.state in self.NON_OCCUPIED_PORT_STATES)
            )

    # ═════════════════════════════════════════════════════════════════════════════
    # Onchange Methods
    # ═════════════════════════════════════════════════════════════════════════════
    @api.onchange('box_group_id')
    def _onchange_box_group_id(self):        
        if not self.box_group_id:
            self.identifier = False
            _logger.info("onchange_box_group_id: Sin grupo, borrando identifier")
            return

        # Generar identificador basado en el grupo
        next_letter = self._get_next_letter_for_group(self.box_group_id)
        new_identifier = self._build_identifier(self.box_group_id, next_letter)
        self.identifier = new_identifier
        _logger.info(f"onchange_box_group_id: Grupo {self.box_group_id.group_number} seleccionado, identificador generado: {new_identifier}")

    @api.onchange('identifier')
    def _onchange_identifier(self):        
        if not self.identifier and self.box_group_id:
            next_letter = self._get_next_letter_for_group(self.box_group_id)
            new_identifier = self._build_identifier(self.box_group_id, next_letter)
            self.identifier = new_identifier
            _logger.info(f"onchange_identifier: Se regeneró identificador: {new_identifier}")

    # ═════════════════════════════════════════════════════════════════════════════
    # CRUD Methods
    # ═════════════════════════════════════════════════════════════════════════════
    @api.model
    def default_get(self, fields_list):       
        defaults = super().default_get(fields_list)                
        box_group_id = self.env.context.get('default_box_group_id')
        
        if box_group_id:
            try:
                group = self.env['wigo.ftth.box.group'].browse(box_group_id)
                _logger.info(f"default_get: box_group_id encontrado en contexto: {box_group_id} (grupo {group.id})")
                if group.exists():
                    next_letter = self._get_next_letter_for_group(group)
                    identifier = self._build_identifier(group, next_letter)
                    defaults['identifier'] = identifier
                    defaults['box_group_id'] = box_group_id
                    _logger.info(f"default_get: Identificador pre-generado: {identifier}")
            except Exception as e:
                _logger.exception(f"Error en default_get: {e}")
        else:
            _logger.info(f"default_get: Sin box_group_id en contexto, identifier se generará en onchange")
        
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para generar identificadores únicos.

        Importante: cuando se crean múltiples NAPs en un solo create_multi (ej. wizard),
        no se puede depender de búsquedas en BD por cada `vals`, porque los registros
        aún no existen y se repetiría la misma letra (01A, 01A, 01A...).

        Esta implementación asigna letras secuenciales por grupo dentro del mismo batch.
        """
        self._assign_identifiers_for_create(vals_list)
        return super().create(vals_list)

    def _assign_identifiers_for_create(self, vals_list):
        """Asigna `identifier` a los `vals` que no lo traen y tienen `box_group_id`.

        - Hace 1 búsqueda para obtener identificadores existentes por grupo.
        - Asigna letras A..Z en el orden en el que llegan los `vals`.
        - Evita duplicados en create_multi.
        """
        vals_by_group = {}
        for vals in vals_list:
            if vals.get('identifier') or not vals.get('box_group_id'):
                continue
            vals_by_group.setdefault(vals['box_group_id'], []).append(vals)

        if not vals_by_group:
            return

        group_ids = list(vals_by_group.keys())
        groups = self.env['wigo.ftth.box.group'].browse(group_ids)
        group_by_id = {g.id: g for g in groups if g.exists()}

        used_letters_by_group = {gid: set() for gid in group_ids}
        existing_rows = self.search_read(
            [('box_group_id', 'in', group_ids), ('identifier', '!=', False)],
            ['box_group_id', 'identifier'],
        )
        for row in existing_rows:
            group_id = row.get('box_group_id') and row['box_group_id'][0]
            identifier = row.get('identifier') or ''
            if not group_id or not identifier:
                continue

            last_char = identifier[-1]
            if last_char.isalpha():
                used_letters_by_group.setdefault(group_id, set()).add(last_char.upper())

        for group_id, group_vals in vals_by_group.items():
            group = group_by_id.get(group_id)
            if not group:
                continue

            used_letters = used_letters_by_group.get(group_id, set())
            next_letter = self.FIRST_LETTER if not used_letters else chr(ord(sorted(used_letters)[-1]) + 1)

            for vals in group_vals:
                if not next_letter.isalpha() or ord(next_letter) > ord('Z'):
                    raise UserError(
                        'No se pueden generar más cajas en este grupo: se alcanzó el límite de letras (A-Z).\n'
                        'Cree un nuevo grupo o ajuste la numeración del grupo actual.'
                    )

                vals['identifier'] = self._build_identifier(group, next_letter)
                next_letter = chr(ord(next_letter) + 1)

    # ═════════════════════════════════════════════════════════════════════════════
    # Display Methods
    # ═════════════════════════════════════════════════════════════════════════════
    def name_get(self):
        return [
            (
                record.id,
                f"NAP {record.identifier} ({record.port_capacity}p)"
            )
            for record in self
        ]

    # ═════════════════════════════════════════════════════════════════════════════
    # Action Methods
    # ═════════════════════════════════════════════════════════════════════════════
    def action_generate_ports(self):
      
        for box in self:
            self._generate_box_ports(box)

        return True

    def action_open_generate_ports_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmación',
            'res_model': 'wigo.generic.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': '¿Está seguro que desea generar los puertos?',
                'default_model_name': self._name,
                'default_method_name': 'action_generate_ports',
                'default_res_id': self.id,
            }
        }

    # ═════════════════════════════════════════════════════════════════════════════
    # Private Methods
    # ═════════════════════════════════════════════════════════════════════════════
    def _auto_generate_identifier(self, vals):
        
        if vals.get('identifier') or not vals.get('box_group_id'):
            return

        group = self.env['wigo.ftth.box.group'].browse(vals['box_group_id'])
        next_letter = self._get_next_letter_for_group(group)
        vals['identifier'] = self._build_identifier(group, next_letter)

    def _get_next_letter_for_group(self, group):
       
        _logger.info(f"=== _get_next_letter_for_group llamado para grupo: {group.id} ({group.group_number}) ===")
        real_group_id = group._origin.id if group._origin else group.id
        existing_boxes = self.search([
            ('box_group_id', '=', real_group_id),
            ('identifier', '!=', False)
        ])

        _logger.info(f"Cajas encontradas para grupo {group.group_number}: {len(existing_boxes)}")
        for box in existing_boxes:
            _logger.info(f"  - Caja: {box.identifier} (grupo: {box.box_group_id.group_number})")

        existing_letters = self._extract_letters_from_identifiers(existing_boxes)
        _logger.info(f"Letras extraídas para grupo {group.group_number}: {existing_letters}")

        if not existing_letters:
            _logger.info(f"No hay cajas en grupo {group.group_number}, devolviendo: {self.FIRST_LETTER}")
            return self.FIRST_LETTER

        last_letter = sorted(existing_letters)[-1]
        next_letter = chr(ord(last_letter) + 1)
        _logger.info(f"Última letra en grupo {group.group_number}: {last_letter}, siguiente: {next_letter}")
        return next_letter

    def _extract_letters_from_identifiers(self, boxes):       
        letters = []

        for box in boxes:
            try:
                last_char = box.identifier[-1]
                if last_char.isalpha():
                    letters.append(last_char.upper())
            except (IndexError, AttributeError):
                continue

        return letters

    def _build_identifier(self, group, letter):
       
        identifier = f"{group.group_number}{letter}"
        _logger.info(f"_build_identifier: grupo {group.group_number} + letra {letter} = {identifier}")
        return identifier

    def _generate_box_ports(self, box):
       
        if not box.port_capacity:
            return        
        if box.port_ids:
            return

        total_ports = int(box.port_capacity)
        port_values = [
            {
                'box_id': box.id,
                'port_number': str(i).zfill(2),
                'state': self.STATE_FREE
            }
            for i in range(1, total_ports + 1)
        ]

        self.env['wigo.ftth.box.port'].create(port_values)

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        if field_name == 'olt_id':
            domain = kwargs.get('search_domain', [])

            records = self.search(domain + [('olt_id', '!=', False)])

            grouped = {}

            for rec in records:
                olt = rec.olt_id
                if not olt:
                    continue

                name = olt.olt_code or olt.display_name or f'OLT {olt.id}'

                if name not in grouped:
                    grouped[name] = {
                        'ids': set(),
                        'count': 0,
                    }

                grouped[name]['ids'].add(olt.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': list(data['ids'])[0],  # 🔥 ID real
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('olt_id', 'in', list(data['ids']))],  # 🔥 clave
                })

            return {
                'parent_field': None,
                'values': values,
            }

        if field_name == 'olt_port_id':
            domain = kwargs.get('search_domain', [])
            records = self.search(domain + [('olt_port_id', '!=', False)])

            grouped = {}
            for rec in records:
                port = rec.olt_port_id
                if not port:
                    continue

                name = port.interface_port or f'Puerto {port.port_number}'
                grouped.setdefault(name, {'ids': set(), 'count': 0})
                grouped[name]['ids'].add(port.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': name,
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('olt_port_id', 'in', list(data['ids']))],
                })

            return {
                'parent_field': None,
                'values': values,
            }

        if field_name == 'box_group_id':
            domain = kwargs.get('search_domain', [])
            records = self.search(domain + [('box_group_id', '!=', False)])

            grouped = {}
            for rec in records:
                group = rec.box_group_id
                if not group:
                    continue

                name = group.group_number or group.display_name
                grouped.setdefault(name, {'ids': set(), 'count': 0})
                grouped[name]['ids'].add(group.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': name,
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('box_group_id', 'in', list(data['ids']))],
                })

            return {
                'parent_field': None,
                'values': values,
            }

        return super().search_panel_select_range(field_name, **kwargs)



class FtthBoxPort(models.Model):
   
    _name = 'wigo.ftth.box.port'
    _inherit = ['wigo.ftth.sync.mixin']
    _description = 'Puerto de Caja FTTH'
    _rec_name = 'port_number'
    _order = 'box_id, port_number'

    _SYNC_CONTEXT_KEY = 'skip_sync'
    _SYNC_FIELDS = ('subinterface_id', 'state')
    _RELEASE_STATES_ON_UNLINK = ('occupied', 'allocated', 'reserved', 'active')

    box_id = fields.Many2one('wigo.ftth.box', string='Caja NAP', required=True, ondelete='cascade')
    port_number = fields.Char(string='Nº Puerto', required=True)
    active = fields.Boolean(string="Activo", default=True, required=True)
    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT',
        compute='_compute_olt_id',
        store=True
    )
    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto OLT',
        compute='_compute_olt_port_id',
        store=True
    )
    box_group_id = fields.Many2one(
        'wigo.ftth.box.group',
        string='Grupo de Caja',
        compute='_compute_box_group_id',
        store=True
    )
    state = fields.Selection([
        ('free', 'Libre'),
        ('occupied', 'Infraestructura'),
        ('allocated', 'Asignada a OT'),
        ('reserved', 'En proceso de activación'),
        ('active', 'Activa (cliente funcionando)'),
    ], string='Estado')
    notes = fields.Html(string='Notas')
    subinterface_id = fields.Many2one(
        'wigo.ftth.subinterface',
        string='Subinterfaz OLT asignada',
        domain="[('olt_port_id', '=', olt_port_id), ('state', '=', 'free')]"
    )

    # =========================
    # Compute
    # =========================

    @api.depends('box_id', 'box_id.box_group_id', 'box_id.box_group_id.olt_port_id')
    def _compute_olt_port_id(self):
        for record in self:
            record.olt_port_id = (
                record.box_id.box_group_id.olt_port_id
                if record.box_id and record.box_id.box_group_id
                else False
            )

    @api.depends('box_id', 'box_id.box_group_id')
    def _compute_box_group_id(self):
        for record in self:
            record.box_group_id = record.box_id.box_group_id if record.box_id else False

    @api.depends('box_id', 'box_id.box_group_id', 'box_id.box_group_id.odn_id', 'box_id.box_group_id.odn_id.olt_id')
    def _compute_olt_id(self):
        for record in self:
            record.olt_id = (
                record.box_id.box_group_id.odn_id.olt_id
                if record.box_id and record.box_id.box_group_id and record.box_id.box_group_id.odn_id
                else False
            )

    # =========================
    # ORM Overrides
    # =========================

    def write(self, vals):
        
        if self.env.context.get(self._SYNC_CONTEXT_KEY):
            return super().write(vals)

        regular_vals, sync_vals = self._split_write_vals(vals)

        if regular_vals:
            super().write(regular_vals)

        if 'subinterface_id' in sync_vals:
            self._apply_subinterface_sync(sync_vals.get('subinterface_id'))
        elif 'state' in sync_vals:
            super(FtthBoxPort, self).write(sync_vals)

        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        SubinterfaceModel = self.env['wigo.ftth.subinterface']
        for record, vals in zip(records, vals_list):
            subinterface_id = vals.get('subinterface_id')
            if subinterface_id:
                subinterface = SubinterfaceModel.browse(subinterface_id)
                self._sync_link(subinterface, record)

        return records

    def unlink(self):
        if self.env.context.get(self._SYNC_CONTEXT_KEY):
            return super().unlink()

        linked_subinterfaces = self.mapped('subinterface_id').filtered(lambda s: s)
        if linked_subinterfaces:
            releasable_subinterfaces = linked_subinterfaces.filtered(
                lambda s: s.state in self._RELEASE_STATES_ON_UNLINK
            )
            if releasable_subinterfaces:
                releasable_subinterfaces.with_context(skip_sync=True).write({
                    'box_port_id': False,
                    'box_id': False,
                    'box_group_id': False,
                    'state': 'free',
                })

            remaining_subinterfaces = linked_subinterfaces - releasable_subinterfaces
            if remaining_subinterfaces:
                remaining_subinterfaces.with_context(skip_sync=True).write({
                    'box_port_id': False,
                    'box_id': False,
                    'box_group_id': False,
                })

        return super().unlink()

    # =========================
    # Onchange
    # =========================

    @api.onchange('box_id')
    def _onchange_box_id(self):
        if not self.box_id:
            self.port_number = False
            return

        next_port_number = self._get_next_port_number_for_box(self.box_id.id)
        self.port_number = str(next_port_number).zfill(2)

    # =========================
    # Constraints
    # =========================

    @api.constrains('box_id', 'port_number')
    def _check_unique_port(self):
        for record in self:
            duplicate = self.search([
                ('box_id', '=', record.box_id.id),
                ('port_number', '=', record.port_number),
                ('id', '!=', record.id)
            ], limit=1)
            if duplicate:
                raise ValidationError("Este puerto ya existe en la caja.")
  
    # =========================
    # Display
    # =========================

    def name_get(self):
        result = []
        for record in self:
            box = record.box_id
            box_identifier = (
                getattr(box, 'identifier', False)
                or getattr(box, 'identificador', False)
                or ''
            )
            result.append((record.id, f'{box_identifier} / P{record.port_number}'))
        return result

    # =========================
    # Private helpers
    # =========================

    def _split_write_vals(self, vals):
        regular_vals = {k: v for k, v in vals.items() if k not in self._SYNC_FIELDS}
        sync_vals = {k: v for k, v in vals.items() if k in self._SYNC_FIELDS}
        return regular_vals, sync_vals

    def _apply_subinterface_sync(self, new_subinterface_id):
        SubinterfaceModel = self.env['wigo.ftth.subinterface']

        for record in self:
            if new_subinterface_id:
                subinterface = SubinterfaceModel.browse(new_subinterface_id)
                self._validate_subinterface_available(subinterface, record)
                self._sync_link(subinterface, record)
            else:
                self._sync_unlink(box_port=record)

    def _validate_subinterface_available(self, subinterface, box_port):
        if subinterface.box_port_id and subinterface.box_port_id.id != box_port.id:
            raise ValidationError(
                f"La subinterfaz {subinterface.code} ya está asignada "
                f"al puerto {subinterface.box_port_id.port_number}."
            )

    def _get_next_port_number_for_box(self, box_id):
      
        rows = self.env['wigo.ftth.box.port'].search_read(
            [('box_id', '=', box_id)],
            ['port_number']
        )

        if not rows:
            return 1

        numbers = [int(row['port_number']) for row in rows if row.get('port_number')]
        return (max(numbers) + 1) if numbers else 1

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        domain = kwargs.get('search_domain', [])

        if field_name == 'olt_id':
            records = self.env['wigo.ftth.box.port'].search(domain + [('olt_id', '!=', False)])
            grouped = {}

            for rec in records:
                olt = rec.olt_id
                if not olt:
                    continue

                name = olt.olt_code or olt.display_name or f'OLT {olt.id}'
                grouped.setdefault(name, {'ids': set(), 'count': 0})
                grouped[name]['ids'].add(olt.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': name,
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('olt_id', 'in', list(data['ids']))],
                })

            return {'parent_field': None, 'values': values}

        if field_name == 'olt_port_id':
            records = self.env['wigo.ftth.box.port'].search(domain + [('olt_port_id', '!=', False)])
            grouped = {}

            for rec in records:
                port = rec.olt_port_id
                if not port:
                    continue

                name = port.interface_port or f'Puerto {port.port_number}'
                grouped.setdefault(name, {'ids': set(), 'count': 0})
                grouped[name]['ids'].add(port.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': name,
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('olt_port_id', 'in', list(data['ids']))],
                })

            return {'parent_field': None, 'values': values}

        if field_name == 'box_id':
            records = self.env['wigo.ftth.box.port'].search(domain + [('box_id', '!=', False)])
            grouped = {}

            for rec in records:
                box = rec.box_id
                if not box or not box.identifier:
                    continue

                name = box.identifier
                grouped.setdefault(name, {'ids': set(), 'count': 0})
                grouped[name]['ids'].add(box.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': name,
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('box_id', 'in', list(data['ids']))],
                })

            return {'parent_field': None, 'values': values}

        if field_name == 'box_group_id':
            records = self.env['wigo.ftth.box.port'].search(domain + [('box_group_id', '!=', False)])
            grouped = {}

            for rec in records:
                box_group = rec.box_group_id
                if not box_group:
                    continue

                name = box_group.group_number
                grouped.setdefault(name, {'ids': set(), 'count': 0})
                grouped[name]['ids'].add(box_group.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': name,
                    'display_name': name,
                    'count': data['count'],
                    '__domain': [('box_group_id', 'in', list(data['ids']))],
                })

            return {'parent_field': None, 'values': values}

        return super().search_panel_select_range(field_name, **kwargs)


class FtthSubinterface(models.Model):
    _name = 'wigo.ftth.subinterface'
    _inherit = ['wigo.ftth.sync.mixin']
    _description = 'Subinterfaz OLT'
    _order = 'olt_port_id, subinterface_number'
    _RELEASE_STATES_ON_UNLINK = ('occupied', 'allocated', 'reserved', 'active')

    _vlan_range_check = models.Constraint(
        'CHECK (vlan_id BETWEEN 1 AND 4094)',
        'VLAN ID must be between 1 and 4094.'
    )

    # ─────────────────────────────────────────────────────────────
    # FIELDS
    # ─────────────────────────────────────────────────────────────
    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto OLT',
        required=True,
        ondelete='restrict'
    )

    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT',
        compute='_compute_olt_id',
        store=True,
        help='OLT asociada (obtenida del puerto OLT)'
    )

    box_group_id = fields.Many2one('wigo.ftth.box.group', string='Grupo')
    box_id = fields.Many2one('wigo.ftth.box', string='Caja')

    box_port_id = fields.Many2one(
        'wigo.ftth.box.port',
        string='Puerto de Caja',
        domain="[('state', '=', 'free')]"
    )

    subinterface_number = fields.Integer(string='Nº Subinterfaz', required=True)

    prefix = fields.Char(
        string='Prefijo',
        required=True,
        default='gpon-olt',
        help='Prefijo editable del nombre de la subinterfaz. Ej: gpon-olt'
    )

    port_identifier = fields.Char(
        string='Identificador de puerto',
        compute='_compute_port_identifier',
        store=True,
        help='Identificador del puerto (ej: 1/1/1), derivado de la interfaz del puerto OLT.'
    )

    # IEEE 802.1Q VLAN identifier associated to this subinterface.
    vlan_id = fields.Integer(
        string='VLAN',
        required=True,
        index=True,
        default=1,
        help='IEEE 802.1Q VLAN ID (valid range: 1-4094).',
    )

    # UI helper: keep a plain string representation (no thousands separators like 4.000).
    vlan_text = fields.Char(
        string='VLAN',
        compute='_compute_vlan_text',
        inverse='_inverse_vlan_text',
        store=False,
        help='VLAN ID sin separadores de miles (ej: 4000).',
    )

    code = fields.Char(
        string='Código',
        compute='_compute_code',
        store=True,
        index=True
    )

    active = fields.Boolean(string="Activo", default=True, required=True)

    state = fields.Selection([
        ('free', 'Libre'),
        ('occupied', 'Infraestructura'),        
        ('allocated', 'Asignada a OT'),
        ('reserved', 'En proceso de activación'),
        ('active', 'Activa (cliente funcionando)'),
    ], string='Estado', default='free')

    notes = fields.Html(string='Notas')

    client_service_id = fields.Many2one(
        'wigo.ftth.client.service',
        string='Cliente asignado',
        readonly=True
    )

    onu_id = fields.Many2one(
        'wigo.ftth.onu',
        string='ONU asignada',
        readonly=True
    )

    # ─────────────────────────────────────────────────────────────
    # COMPUTE METHODS
    # ─────────────────────────────────────────────────────────────
    @api.depends('prefix', 'port_identifier', 'olt_port_id', 'olt_port_id.interface_port', 'subinterface_number')
    def _compute_code(self):
        for rec in self:
            rec.code = self._build_code(rec)

    @api.depends('olt_port_id', 'olt_port_id.interface_port')
    def _compute_port_identifier(self):
        for rec in self:
            rec.port_identifier = rec._extract_port_identifier(
                rec.olt_port_id.interface_port if rec.olt_port_id else False
            )

    @api.depends('olt_port_id')
    def _compute_olt_id(self):
        for rec in self:
            rec.olt_id = rec.olt_port_id.olt_id if rec.olt_port_id else False

    @api.depends('vlan_id')
    def _compute_vlan_text(self):
        for rec in self:
            rec.vlan_text = str(rec.vlan_id) if rec.vlan_id else ''

    def _inverse_vlan_text(self):
        for rec in self:
            raw = (rec.vlan_text or '').strip()
            if not raw:
                rec.vlan_id = False
                continue

            # Accept common separators but store as plain integer.
            normalized = raw.replace('.', '').replace(',', '').replace(' ', '')
            if not normalized.isdigit():
                raise ValidationError('La VLAN debe ser un número entero (1-4094).')

            rec.vlan_id = int(normalized)

    def _build_code(self, rec):
        if rec.subinterface_number and rec.prefix and rec.port_identifier:
            return f"{rec.prefix}_{rec.port_identifier}:{rec.subinterface_number}"
        if rec.olt_port_id and rec.subinterface_number and rec.olt_port_id.interface_port:
            return f"{rec.olt_port_id.interface_port}:{rec.subinterface_number}"
        return ''

    def _extract_port_identifier(self, interface_port):
        if not interface_port:
            return False
        text = str(interface_port)
        if '_' in text:
            return text.split('_', 1)[1]
        return text

    # ─────────────────────────────────────────────────────────────
    # CONSTRAINTS
    # ─────────────────────────────────────────────────────────────
    @api.constrains('olt_port_id', 'subinterface_number')
    def _check_unique_subinterface(self):
        for rec in self:
            if self._exists_duplicate(rec):
                raise ValidationError(
                    f"La subinterfaz {rec.code} ya existe en este puerto (RN-02)."
                )

    @api.constrains('vlan_id')
    def _check_vlan_id_range(self):
        """Ensure VLAN ID is within the IEEE 802.1Q valid range."""
        for rec in self:
            if rec.vlan_id is None:
                raise ValidationError('VLAN ID is required.')
            if rec.vlan_id < 1 or rec.vlan_id > 4094:
                raise ValidationError('VLAN ID must be between 1 and 4094.')

    @api.constrains('code', 'olt_id', 'olt_port_id')
    def _check_unique_code(self):
        for rec in self:
            if not rec.code or not rec.olt_id or not rec.olt_port_id:
                continue
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('olt_id', '=', rec.olt_id.id),
                ('olt_port_id', '=', rec.olt_port_id.id),
                ('code', '=', rec.code),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    f"La subinterfaz '{rec.code}' ya existe para la OLT y puerto PON seleccionados."
                )

    def _exists_duplicate(self, rec):
        return self.search([
            ('olt_port_id', '=', rec.olt_port_id.id),
            ('subinterface_number', '=', rec.subinterface_number),
            ('id', '!=', rec.id),
        ], limit=1)

    # ─────────────────────────────────────────────────────────────
    # ORM OVERRIDES
    # ─────────────────────────────────────────────────────────────
    def write(self, vals):
        if self.env.context.get('skip_sync'):
            return super().write(vals)

        sync_vals, other_vals = self._split_vals(vals)

        result = True

        if other_vals:
            result = super().write(other_vals)

        if 'box_port_id' in sync_vals:
            self._handle_box_port_sync(sync_vals['box_port_id'])
        elif 'state' in sync_vals:
            result = super().write(sync_vals)

        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('prefix'):
                if vals.get('olt_port_id'):
                    port = self.env['wigo.ftth.olt.port'].browse(vals['olt_port_id'])
                    vals['prefix'] = port.prefix or 'gpon-olt'
                else:
                    vals['prefix'] = 'gpon-olt'

        records = super().create(vals_list)
        BoxPort = self.env['wigo.ftth.box.port']

        for rec, vals in zip(records, vals_list):
            if vals.get('box_port_id'):
                box_port = BoxPort.browse(vals['box_port_id'])
                self._sync_link(rec, box_port)

        return records

    def unlink(self):
        if self.env.context.get('skip_sync'):
            return super().unlink()

        linked_box_ports = self.mapped('box_port_id').filtered(lambda p: p)
        if linked_box_ports:
            releasable_ports = linked_box_ports.filtered(
                lambda p: p.state in self._RELEASE_STATES_ON_UNLINK
            )
            if releasable_ports:
                releasable_ports.with_context(skip_sync=True).write({
                    'subinterface_id': False,
                    'state': 'free',
                })

            remaining_ports = linked_box_ports - releasable_ports
            if remaining_ports:
                remaining_ports.with_context(skip_sync=True).write({
                    'subinterface_id': False,
                })

        return super().unlink()

    # ─────────────────────────────────────────────────────────────
    # SYNC LOGIC
    # ─────────────────────────────────────────────────────────────
    def _split_vals(self, vals):
        sync_fields = {'box_port_id', 'state'}
        sync_vals = {k: v for k, v in vals.items() if k in sync_fields}
        other_vals = {k: v for k, v in vals.items() if k not in sync_fields}
        return sync_vals, other_vals

    def _handle_box_port_sync(self, new_box_port_id):
        BoxPort = self.env['wigo.ftth.box.port']

        for rec in self:
            if new_box_port_id:
                new_box_port = BoxPort.browse(new_box_port_id)
                self._validate_box_port_availability(rec, new_box_port)
                self._sync_link(rec, new_box_port)
            else:
                self._sync_unlink(subinterface=rec)

    def _validate_box_port_availability(self, rec, box_port):
        if box_port.subinterface_id and box_port.subinterface_id.id != rec.id:
            raise ValidationError(
                f"El puerto {box_port.port_number} de la caja "
                f"{box_port.box_id.identificador} ya está asignado "
                f"a la subinterfaz {box_port.subinterface_id.code}."
            )

    # ─────────────────────────────────────────────────────────────
    # DISPLAY METHODS
    # ─────────────────────────────────────────────────────────────
    @api.depends('code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.code or f"Sub#{rec.id}"

    def name_get(self):
        return [(rec.id, rec.code or f"Sub#{rec.id}") for rec in self]

    # ─────────────────────────────────────────────────────────────
    # ONCHANGE METHODS
    # ─────────────────────────────────────────────────────────────
    @api.onchange('olt_port_id')
    def _onchange_olt_port(self):
        if not self.olt_port_id:
            self.subinterface_number = False
            self.code = False
            self.port_identifier = False
            return

        next_number = self._get_next_subinterface_number(self.olt_port_id.id)
        self.subinterface_number = next_number
        if not self.prefix:
            self.prefix = self.olt_port_id.prefix or 'gpon-olt'
        self.port_identifier = self._extract_port_identifier(self.olt_port_id.interface_port)
        self.code = self._build_onchange_code(next_number)

        self._reset_box_related_fields()

    @api.onchange('box_group_id')
    def _onchange_box_group(self):
        self.box_id = False
        self.box_port_id = False

    @api.onchange('box_id')
    def _onchange_box(self):
        self.box_port_id = False

    @api.onchange('prefix', 'subinterface_number', 'olt_port_id')
    def _onchange_name_parts(self):
        if self.olt_port_id and self.subinterface_number:
            self.code = self._build_onchange_code(self.subinterface_number)

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────
    def _get_next_subinterface_number(self, olt_port_id):
        subinterfaces = self.search([
            ('olt_port_id', '=', olt_port_id)
        ])

        numbers = [int(s.subinterface_number) for s in subinterfaces if s.subinterface_number]
        return (max(numbers) + 1) if numbers else 1

    def _build_onchange_code(self, number):
        identifier = self._extract_port_identifier(self.olt_port_id.interface_port)
        if self.prefix and identifier:
            return f"{self.prefix}_{identifier}:{number}"
        if self.olt_port_id.interface_port:
            return f"{self.olt_port_id.interface_port}:{number}"
        return f"{self.prefix or 'gpon-olt'}_{self.olt_port_id.port_number}:{number}"

    def _reset_box_related_fields(self):
        self.box_group_id = False
        self.box_id = False
        self.box_port_id = False
    
    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        if field_name == 'olt_port_id':
            groups = self.env['wigo.ftth.olt.port'].read_group(
                domain=[],
                fields=['interface_port', 'id:min'],
                groupby=['interface_port'],
                lazy=False,
            )

            values = []
            for g in groups:
                interface = g.get('interface_port')

                if not interface:
                    continue

                display_name = interface
                values.append({
                    'id': interface,
                    'display_name': display_name,
                    'count': g.get('__count', 0),
                })

            return {
                'parent_field': None,
                'values': values,
            }

        if field_name == 'box_group_id':
            domain = kwargs.get('search_domain', [])

            groups = self.env['wigo.ftth.subinterface'].read_group(
                domain=domain + [('box_group_id', '!=', False)],
                fields=['box_group_id'],
                groupby=['box_group_id'],
                lazy=False,
            )

            grouped_by_name = {}

            for g in groups:
                data = g.get('box_group_id')
                if not data:
                    continue

                name = data[1]
                count = g.get('__count', 0)

                if name not in grouped_by_name:
                    grouped_by_name[name] = {
                        'id': name,  # 🔥 usamos el nombre como ID
                        'display_name': name,
                        'count': count,
                    }
                else:
                    grouped_by_name[name]['count'] += count

            return {
                'parent_field': None,
                'values': list(grouped_by_name.values()),
            }
        if field_name == 'box_id':
            domain = kwargs.get('search_domain', [])

            records = self.env['wigo.ftth.subinterface'].search(
                domain + [('box_id', '!=', False)]
            )

            grouped = {}

            for rec in records:
                box = rec.box_id
                if not box or not box.identifier:
                    continue

                name = box.identifier  

                if name not in grouped:
                    grouped[name] = {
                        'ids': set(),
                        'count': 0,
                    }

                grouped[name]['ids'].add(box.id)
                grouped[name]['count'] += 1

            values = []
            for name, data in grouped.items():
                values.append({
                    'id': list(data['ids'])[0], 
                    'display_name': name,       
                    'count': data['count'],
                    '__domain': [('box_id', 'in', list(data['ids']))],  # 🔥 clave
                })

            return {
                'parent_field': None,
                'values': values,
            }

        return super().search_panel_select_range(field_name, **kwargs)        