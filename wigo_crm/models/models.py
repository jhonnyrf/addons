from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class WigoZone(models.Model):
    _name = 'wigo.zone'
    _description = 'Zona Wigo'
    _order = 'name'

    # ==========================================================================
    # Fields
    # ==========================================================================
    name = fields.Char(string="Nombre", required=True, index=True)
    active = fields.Boolean(string="Activo", default=True)

    # ==========================================================================
    # Statistics (Computed - no direct dependency)
    # ==========================================================================
    box_group_count = fields.Integer(
        compute='_compute_box_group_count',
        string='Grupos',
        help='Cantidad de grupos de cajas en esta zona'
    )

    # ==========================================================================
    # Coverage Fields
    # ==========================================================================
    has_coverage = fields.Boolean(
        compute='_compute_has_coverage',
        store=True,
        string='Tiene Cobertura',
        help='Indica si la zona tiene al menos un grupo de cajas asociado'
    )

    coverage_status = fields.Selection([
        ('no_coverage', 'Sin Cobertura'),
        ('available', 'Disponible'),
        ('saturated', 'Saturado'),
    ],
        compute='_compute_coverage_status',
        store=True,
        string='Estado de Cobertura',
        help='Estado actual de cobertura de la zona basado en capacidad'
    )

    total_boxes = fields.Integer(
        compute='_compute_coverage_stats',
        store=True,
        string='Total Cajas',
        help='Cantidad total de cajas NAP en la zona'
    )

    total_ports = fields.Integer(
        compute='_compute_coverage_stats',
        store=True,
        string='Total Puertos',
        help='Cantidad total de puertos disponibles en la zona'
    )

    _sql_constraints = [
        ('wigo_zone_name_uniq', 'unique(name)', 'La zona ya existe.'),
    ]

    # ==========================================================================
    # Private Helpers
    # ==========================================================================

    def _get_box_group_model(self):
        """Safely get box group model."""
        return self.env.get('wigo.ftth.box.group')

    def _get_zone_box_groups(self, zone, model):
        """Get box groups for a zone."""
        return model.search([('zona_id', '=', zone.id)])

    def _compute_total_ports_used(self, box_groups):
        """Compute used ports across all box groups."""
        used_ports = 0

        for group in box_groups:
            for box in group.box_ids:
                used_ports += len(
                    box.port_ids.filtered(lambda p: p.state == 'occupied')
                )

        return used_ports

    # ==========================================================================
    # Computed Methods
    # ==========================================================================

    def _compute_box_group_count(self):
        """Compute number of box groups."""
        model = self._get_box_group_model()

        for zone in self:
            if not model:
                zone.box_group_count = 0
                continue

            zone.box_group_count = model.search_count([
                ('zona_id', '=', zone.id)
            ])

    def _compute_has_coverage(self):
        """Determine if zone has coverage."""
        model = self._get_box_group_model()

        for zone in self:
            if not model:
                zone.has_coverage = False
                continue

            zone.has_coverage = model.search_count([
                ('zona_id', '=', zone.id)
            ]) > 0

    def _compute_coverage_status(self):
        """
        Coverage status:
        - no_coverage
        - available
        - saturated
        """
        model = self._get_box_group_model()

        for zone in self:
            if not model:
                zone.coverage_status = 'no_coverage'
                continue

            box_groups = self._get_zone_box_groups(zone, model)

            if not box_groups:
                zone.coverage_status = 'no_coverage'
                continue

            total_ports = sum(bg.total_puertos for bg in box_groups)

            if total_ports == 0:
                zone.coverage_status = 'available'
                continue

            used_ports = self._compute_total_ports_used(box_groups)

            usage_percentage = (used_ports / total_ports) * 100

            zone.coverage_status = (
                'saturated' if usage_percentage >= 90 else 'available'
            )

    def _compute_coverage_stats(self):
        """Compute total boxes and ports."""
        model = self._get_box_group_model()

        for zone in self:
            if not model:
                zone.total_boxes = 0
                zone.total_ports = 0
                continue

            box_groups = self._get_zone_box_groups(zone, model)

            zone.total_boxes = sum(len(bg.box_ids) for bg in box_groups)
            zone.total_ports = sum(bg.total_puertos for bg in box_groups)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    zona = fields.Char(string="Zona")

    zona_id = fields.Many2one(
        'wigo.zone',
        string="Zona",
        compute='_compute_zona_id',
        inverse='_inverse_zona_id',
        store=False,
        help="Seleccione una zona existente o cree una nueva.",
    )

    direccion = fields.Char(
        string="Dirección",
        help="Dirección exacta del cliente",
    )

    ubicacion = fields.Char(
        string="Ubicación",
        help="Pega aquí el enlace de Google Maps",
    )

    coordenadas = fields.Char(
        string="Coordenadas",
        help="Pega las coordenadas de ubicacion (latitud, longitud).",
    )

    plan_id = fields.Many2one(
        'internet.plan',
        string="Plan contratado",
        domain="[('active', '=', True)]",
        help="Plan de internet asociado al cliente",
    )

    codigo_cliente = fields.Char(
        string="Código de cliente",
        help="Código interno asignado al cliente activo. Formato: CF-001",
        copy=False,
        tracking=True,
    )
    contract_id = fields.Many2one(
        'customer.contract',
        string="Contrato",
        readonly=True,
        copy=False,
    )
    contract_state = fields.Selection(
        related='contract_id.state',
        string="Estado del contrato",
        store=True,      # store=True permite filtrar/agrupar en vistas
    )
    contract_name = fields.Char(
        related='contract_id.name',
        string="Código de contrato",
    )
    contract_plan_id = fields.Many2one(
        related='contract_id.plan_id',
        string="Plan (contrato)",
        store=True,
    )

    contract_date = fields.Date(
        related='contract_id.contract_date',
        string="Fecha de contrato",
        store=True,
    )

    contract_installation_date = fields.Date(
        related='contract_id.installation_date',
        string="Fecha de instalación",
        store=True,
    )
    contract_count = fields.Integer(
        string="Contratos",
        compute='_compute_contract_count',
    )
        # ─── Smart button count ───────────────────────────────────────

    contract_count = fields.Integer(
        string="Contratos",
        compute='_compute_contract_count',
    )

    @api.depends('contract_id')
    def _compute_contract_count(self):
        for lead in self:
            lead.contract_count = 1 if lead.contract_id else 0

    @api.depends('zona')
    def _compute_zona_id(self):
        Zone = self.env['wigo.zone']
        for lead in self:
            value = (lead.zona or '').strip()
            if not value:
                lead.zona_id = False
                continue
            zone = Zone.search([('name', '=ilike', value)], limit=1)
            if not zone:
                zone = Zone.create({'name': value})
            lead.zona_id = zone

    def _inverse_zona_id(self):
        for lead in self:
            lead.zona = lead.zona_id.name if lead.zona_id else False

    @api.constrains('codigo_cliente')
    def _check_codigo_cliente(self):
        for rec in self:
            if not rec.codigo_cliente:
                continue
            codigo = rec.codigo_cliente.strip()
            if not re.match(r'^CF-\d+$', codigo):
                raise ValidationError(
                    "El código de cliente debe tener el formato CF-001, CF-023, etc."
                )
            duplicado = self.search([
                ('codigo_cliente', '=', codigo),
                ('id', '!=', rec.id),
            ], limit=1)
            if duplicado:
                nombre = duplicado.partner_id.name or duplicado.contact_name or "sin nombre"
                raise ValidationError(
                    f"El código '{codigo}' ya está asignado al cliente '{nombre}'."
                )

    # ── Método privado: lógica de creación ───────────────────────
    def _create_partner_plan_if_needed(self):
        """
        Si el lead tiene partner_id, plan_id y codigo_cliente,
        crea un partner.plan en el contacto (si no existe ya ese código).
        """
        PlanModel = self.env['partner.plan']
        for lead in self:
            if not (lead.partner_id and lead.plan_id and lead.codigo_cliente):
                continue
            codigo = lead.codigo_cliente.strip().upper()
            existing = PlanModel.search([
                ('codigo_cliente', '=ilike', codigo)
            ], limit=1)
            if existing:
                continue
            PlanModel.create({
                'partner_id':     lead.partner_id.id,
                'plan_id':        lead.plan_id.id,
                'codigo_cliente': codigo,
                'date_start':     fields.Date.today(),
                'zona':           lead.zona or '',
                'direccion':      lead.direccion or '',
                'ubicacion':      lead.ubicacion or '',
                'lead_id':        lead.id,
                'state':          'active',
            })

    # ── Método PÚBLICO para el botón XML ─────────────────────────
    def action_register_plan(self):
        """
        Método público llamado desde el botón en la vista.
        Registra el plan contratado en la ficha del contacto.
        """
        self._create_partner_plan_if_needed()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plan registrado',
                'message': 'El plan fue registrado correctamente en el contacto.',
                'type': 'success',
                'sticky': False,
            },
        }
    # ─── Lógica de creación de contrato ──────────────────────────

    def _build_contract_vals(self):
        """Devuelve el dict de valores para crear el contrato desde el lead."""
        self.ensure_one()
        return {
            'partner_id':      self.partner_id.id,
            'lead_id':         self.id,
            'plan_id':         self.plan_id.id,
            'address':         self.direccion or '',
            'location_link':   self.ubicacion or '',
            'coordinates':     self.coordenadas or '',
            'state':           'draft',
        }

    def _create_contract_if_needed(self):
        """Crea el contrato vinculado si no existe. Retorna el contrato."""
        Contract = self.env['customer.contract']
        for lead in self:
            if lead.contract_id:
                continue
            if not (lead.partner_id and lead.plan_id):
                continue
            contract = Contract.create(lead._build_contract_vals())
            lead.contract_id = contract.id
        return self.contract_id

    # ─── Botón manual (fallback / visible solo sin contrato) ─────

    def action_create_contract(self):
        self.ensure_one()
        if self.contract_id:
            raise ValidationError("Este lead ya tiene un contrato.")
        if not self.partner_id:
            raise ValidationError("Debe seleccionar un cliente.")
        if not self.plan_id:
            raise ValidationError("Debe seleccionar un plan.")

        self._create_contract_if_needed()

        # Abrir el contrato recién creado
        return self._action_open_contract()

    # ─── Smart button: abrir contrato ────────────────────────────

    def action_open_contract(self):
        self.ensure_one()
        return self._action_open_contract()

    def _action_open_contract(self):
        self.ensure_one()
        if not self.contract_id:
            return False
        return {
            'type':      'ir.actions.act_window',
            'res_model': 'customer.contract',
            'view_mode': 'form',
            'res_id':    self.contract_id.id,
            'target':    'current',
        }

    def action_set_won(self):
        self.ensure_one()
        if not self.plan_id:
            raise ValidationError("Debe seleccionar el plan contratado antes de marcar el lead como Ganado.")

        res = super().action_set_won()
        return res


    def action_set_won_rainbowman(self):
        self.ensure_one()
        if not self.plan_id:
            raise ValidationError("Debe seleccionar el plan contratado antes de marcar el lead como Ganado.")

        res = super().action_set_won_rainbowman()
        return res


    def _redirect_to_contract(self, fallback):
        if not self.contract_id:
            return fallback

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'target': 'current',
        }

