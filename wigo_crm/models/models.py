from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import logging
_logger = logging.getLogger(__name__)

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
    # Coverage Fields (FTTH real end-to-end)
    # ==========================================================================
    # Nota: todos estos campos comparten el mismo compute para evitar recalcular
    # varias veces en listas/vistas.

    has_coverage = fields.Boolean(
        compute='_compute_coverage_stats',
        search='_search_has_coverage',
        store=False,
        string='Tiene Cobertura',
        help=(
            'Cobertura FTTH REAL (end-to-end): existe infraestructura válida '
            'y hay capacidad libre tanto en NAP (puertos de caja) como en OLT '
            '(subinterfaces disponibles: free u occupied)'
        )
    )

    coverage_status = fields.Selection([
        ('no_coverage', 'Sin Cobertura'),
        ('saturated', 'Saturado'),
        ('warning', 'En riesgo'),
        ('available', 'Disponible'),
    ],
        compute='_compute_coverage_stats',
        search='_search_coverage_status',
        store=False,
        string='Estado de Cobertura',
        help='Estado de cobertura basado en capacidad libre end-to-end y ocupación.'
    )

    # Métricas de capacidad (no almacenadas)
    used_ports = fields.Integer(
        compute='_compute_coverage_stats',
        store=False,
        string='Puertos usados',
        help=(
            "Puertos de caja en estados usados (cualquier estado distinto de 'free' y 'occupied')."
        )
    )

    free_box_ports = fields.Integer(
        compute='_compute_coverage_stats',
        search='_search_free_box_ports',
        store=False,
        string='Puertos disponibles (NAP)',
        help=(
            "Puertos de caja 'no usados' dentro de box groups válidos (estado free u occupied)."
        )
    )

    free_subinterfaces = fields.Integer(
        compute='_compute_coverage_stats',
        search='_search_free_subinterfaces',
        store=False,
        string='Subinterfaces disponibles',
        help=(
            "Subinterfaces 'no usadas' en los puertos OLT asociados a la zona "
            "(estado free u occupied)."
        )
    )

    total_boxes = fields.Integer(
        compute='_compute_coverage_stats',
        store=False,
        string='Total Cajas',
        help='Cantidad total de cajas NAP en la zona (en box groups válidos)'
    )

    total_ports = fields.Integer(
        compute='_compute_coverage_stats',
        store=False,
        string='Total Puertos',
        help='Total de puertos NAP declarados (suma de total_ports de box groups válidos)'
    )

    _sql_constraints = [
        ('wigo_zone_name_uniq', 'unique(name)', 'La zona ya existe.'),
    ]

    # ==========================================================================
    # Private Helpers (FTTH)
    # ==========================================================================

    def _get_ftth_model(self, model_name):
        """Return an FTTH model as sudo() if it exists, else None.

        env.get() returns an *empty recordset* when the model exists.
        Empty recordsets are falsy, so we must check `is None` explicitly.
        """
        model = self.env.get(model_name)
        return model.sudo() if model is not None else None

    def _get_valid_box_groups(self, zones):
        """Return (valid_box_groups, zone_to_port_ids).

        A box group is considered valid for coverage if:
        - belongs to the zone
        - has olt_port_id
        - has odn_id
        - (optional) active=True when the field exists
        """
        BoxGroup = self._get_ftth_model('wigo.ftth.box.group')
        if BoxGroup is None or not zones:
            return None, {}

        domain = [
            ('zone_id', 'in', zones.ids),
            ('olt_port_id', '!=', False),
            ('odn_id', '!=', False),
        ]
        if 'active' in BoxGroup._fields:
            domain.append(('active', '=', True))

        groups = BoxGroup.search(domain)

        zone_to_port_ids = {}
        for g in groups:
            zid = g.zone_id.id
            zone_to_port_ids.setdefault(zid, set())
            if g.olt_port_id:
                zone_to_port_ids[zid].add(g.olt_port_id.id)

        return groups, zone_to_port_ids

    def _get_free_box_ports(self, valid_box_groups):
        """Return dicts: free_box_ports_by_zone, used_ports_by_zone.

        IMPORTANTE:
        - En varias versiones de Odoo, read_group() NO soporta groupby con rutas
          tipo "a.b.c" (dotted). Por eso no agrupamos por zone_id directo.
        - Agregamos por (box_id, state) y luego mapeamos box_id -> zone_id.
        """
        if not valid_box_groups:
            return {}, {}

        BoxPort = self._get_ftth_model('wigo.ftth.box.port')
        Box = self._get_ftth_model('wigo.ftth.box')
        if BoxPort is None or Box is None:
            return {}, {}

        available_states = ['free', 'occupied']

        # Map box_group_id -> zone_id para los grupos válidos
        group_to_zone = {g.id: g.zone_id.id for g in valid_box_groups if g.zone_id}

        # Traer boxes que pertenecen a grupos válidos (sin dotted groupby)
        box_rows = Box.search_read(
            [('box_group_id', 'in', valid_box_groups.ids)],
            ['id', 'box_group_id'],
        )
        if not box_rows:
            return {}, {}

        box_to_zone = {}
        box_ids = []
        for row in box_rows:
            box_id = row.get('id')
            group = row.get('box_group_id')
            group_id = group[0] if isinstance(group, (list, tuple)) and group else None
            zid = group_to_zone.get(group_id)
            if box_id and zid:
                box_to_zone[box_id] = zid
                box_ids.append(box_id)

        if not box_ids:
            return {}, {}

        # Contamos TODOS los estados y clasificamos:
        # - 'free' y 'occupied' => disponibles (no usados)
        # - cualquier otro      => usados
        rg = BoxPort.read_group(
            domain=[
                ('box_id', 'in', box_ids),
                ('state', '!=', False),
            ],
            fields=['box_id', 'state'],
            groupby=['box_id', 'state'],
            lazy=False,
        )

        free_by_zone = {}
        used_by_zone = {}
        for row in rg:
            box = row.get('box_id')
            if not box:
                continue
            box_id = box[0]
            zid = box_to_zone.get(box_id)
            if not zid:
                continue

            state = row.get('state')
            count = row.get('__count', 0) or 0

            if state in ('free', 'occupied'):
                free_by_zone[zid] = free_by_zone.get(zid, 0) + count
            else:
                used_by_zone[zid] = used_by_zone.get(zid, 0) + count

        return free_by_zone, used_by_zone

    def _get_free_subinterfaces(self, zone_to_port_ids):
        """Return dict: free_subinterfaces_by_zone.

        Regla de negocio:
        - state='free'     => libre / no asignada a topología o red
        - state='occupied' => asignada, pero todavía NO usada (también cuenta como disponible)
        - otros estados    => usada

        A zone's relevant ports are the union of olt_port_id in its valid box groups.
        """
        if not zone_to_port_ids:
            return {}

        Subinterface = self._get_ftth_model('wigo.ftth.subinterface')
        if Subinterface is None:
            return {}

        all_port_ids = set()
        for port_ids in zone_to_port_ids.values():
            all_port_ids |= set(port_ids)

        if not all_port_ids:
            return {}

        rg = Subinterface.read_group(
            domain=[
                ('olt_port_id', 'in', list(all_port_ids)),
                ('state', 'in', ['free', 'occupied']),
            ],
            fields=['olt_port_id'],
            groupby=['olt_port_id'],
            lazy=False,
        )

        available_by_port = {
            row['olt_port_id'][0]: (row.get('__count', 0) or 0)
            for row in rg
            if row.get('olt_port_id')
        }

        available_by_zone = {}
        for zid, port_ids in zone_to_port_ids.items():
            available_by_zone[zid] = sum(available_by_port.get(pid, 0) for pid in port_ids)

        return available_by_zone

    def _get_coverage_snapshot(self, zones):
        """Return a dict snapshot of coverage stats for the given zones.

        Importante:
        - Estos campos son compute+store=False.
        - Para poder usar filtros en vistas (domains), Odoo requiere que el
          campo sea *searchable* (store=True o tener método search=...).
        - Este helper calcula los mismos números que `_compute_coverage_stats`,
          pero sin escribir en los registros (solo devuelve un dict).
        """
        snapshot = {
            z.id: {
                'total_boxes': 0,
                'total_ports': 0,
                'used_ports': 0,
                'free_box_ports': 0,
                'free_subinterfaces': 0,
                'has_coverage': False,
                'coverage_status': 'no_coverage',
            }
            for z in zones
        }
        if not zones:
            return snapshot

        valid_groups, zone_to_port_ids = self._get_valid_box_groups(zones)
        if not valid_groups:
            return snapshot

        # total_ports por zona (desde box_group.total_ports)
        rg_ports = valid_groups.read_group(
            domain=[('id', 'in', valid_groups.ids)],
            fields=['zone_id', 'total_ports'],
            groupby=['zone_id'],
            lazy=False,
        )
        total_ports_by_zone = {
            row['zone_id'][0]: (row.get('total_ports', 0) or 0)
            for row in rg_ports
            if row.get('zone_id')
        }

        # total_boxes por zona
        total_boxes_by_zone = {}
        Box = self._get_ftth_model('wigo.ftth.box')
        if Box is not None:
            group_to_zone = {g.id: g.zone_id.id for g in valid_groups if g.zone_id}
            rg_boxes = Box.read_group(
                domain=[('box_group_id', 'in', valid_groups.ids)],
                fields=['box_group_id'],
                groupby=['box_group_id'],
                lazy=False,
            )
            for row in rg_boxes:
                group = row.get('box_group_id')
                if not group:
                    continue
                group_id = group[0]
                zid = group_to_zone.get(group_id)
                if not zid:
                    continue
                total_boxes_by_zone[zid] = total_boxes_by_zone.get(zid, 0) + (row.get('__count', 0) or 0)

        # Puertos NAP disponibles/usados por zona
        free_box_ports_by_zone, used_ports_by_zone = self._get_free_box_ports(valid_groups)

        # Subinterfaces disponibles por zona
        free_sub_by_zone = self._get_free_subinterfaces(zone_to_port_ids)

        for z in zones:
            zid = z.id
            s = snapshot[zid]

            s['total_ports'] = int(total_ports_by_zone.get(zid, 0) or 0)
            s['total_boxes'] = int(total_boxes_by_zone.get(zid, 0) or 0)
            s['used_ports'] = int(used_ports_by_zone.get(zid, 0) or 0)
            s['free_box_ports'] = int(free_box_ports_by_zone.get(zid, 0) or 0)
            s['free_subinterfaces'] = int(free_sub_by_zone.get(zid, 0) or 0)

            # Si no hay box groups válidos para la zona, no hay cobertura
            if zid not in zone_to_port_ids:
                s['coverage_status'] = 'no_coverage'
                s['has_coverage'] = False
                continue

            # Si no hay puertos en absoluto, no hay infraestructura útil
            if s['total_ports'] <= 0 and (s['used_ports'] + s['free_box_ports']) <= 0:
                s['coverage_status'] = 'no_coverage'
                s['has_coverage'] = False
                continue

            # Saturación end-to-end
            if s['free_box_ports'] <= 0 or s['free_subinterfaces'] <= 0:
                s['coverage_status'] = 'saturated'
                s['has_coverage'] = False
                continue

            occupancy = (s['used_ports'] / s['total_ports']) if s['total_ports'] else 0.0
            s['coverage_status'] = 'warning' if occupancy >= 0.80 else 'available'
            s['has_coverage'] = True

        return snapshot

    def _search_has_coverage(self, operator, value):
        if operator not in ('=', '!='):
            return []
        expected = bool(value)
        if operator == '!=':
            expected = not expected

        zones = self.search([])
        snap = self._get_coverage_snapshot(zones)
        ids = [zid for zid, s in snap.items() if bool(s.get('has_coverage')) == expected]
        return [('id', 'in', ids)]

    def _search_coverage_status(self, operator, value):
        if operator in ('=', '!='):
            values = {value}
        elif operator in ('in', 'not in'):
            values = set(value or [])
        else:
            return []

        zones = self.search([])
        snap = self._get_coverage_snapshot(zones)

        if operator in ('!=', 'not in'):
            ids = [zid for zid, s in snap.items() if s.get('coverage_status') not in values]
        else:
            ids = [zid for zid, s in snap.items() if s.get('coverage_status') in values]

        return [('id', 'in', ids)]

    def _search_free_box_ports(self, operator, value):
        return self._search_snapshot_int('free_box_ports', operator, value)

    def _search_free_subinterfaces(self, operator, value):
        return self._search_snapshot_int('free_subinterfaces', operator, value)

    def _search_snapshot_int(self, key, operator, value):
        """Generic search helper for int snapshot keys."""
        if operator not in ('=', '!=', '>', '>=', '<', '<='):
            return []
        try:
            expected = int(value)
        except Exception:
            return []

        def _cmp(actual):
            if operator == '=':
                return actual == expected
            if operator == '!=':
                return actual != expected
            if operator == '>':
                return actual > expected
            if operator == '>=':
                return actual >= expected
            if operator == '<':
                return actual < expected
            if operator == '<=':
                return actual <= expected
            return False

        zones = self.search([])
        snap = self._get_coverage_snapshot(zones)
        ids = [zid for zid, s in snap.items() if _cmp(int(s.get(key, 0) or 0))]
        return [('id', 'in', ids)]

    # ==========================================================================
    # Computed Methods
    # ==========================================================================

    def _compute_box_group_count(self):
        """Compute number of box groups per zone (fast, grouped)."""
        BoxGroup = self._get_ftth_model('wigo.ftth.box.group')
        if BoxGroup is None or not self:
            for z in self:
                z.box_group_count = 0
            return

        domain = [('zone_id', 'in', self.ids)]
        if 'active' in BoxGroup._fields:
            domain.append(('active', '=', True))

        rg = BoxGroup.read_group(domain=domain, fields=['zone_id'], groupby=['zone_id'], lazy=False)
        counts = {row['zone_id'][0]: (row.get('__count', 0) or 0) for row in rg if row.get('zone_id')}

        for zone in self:
            zone.box_group_count = counts.get(zone.id, 0)

    # Compat (si alguna parte del código llama estos computes directamente)
    def _compute_has_coverage(self):
        self._compute_coverage_stats()

    def _compute_coverage_status(self):
        self._compute_coverage_stats()

    def _compute_coverage_stats(self):
        """Compute end-to-end coverage and stats for zones.

        Reglas (resumen):
        - Infra válida: box_group en zona con olt_port_id y odn_id.
        - Cobertura real: además debe haber puertos NAP libres y subinterfaces disponibles (free/occupied).
        - Estados:
          * no_coverage: no hay infraestructura válida (o sin puertos)
          * saturated: no hay capacidad (free_box_ports==0 o free_subinterfaces==0)
          * warning: ocupación >= 80%
          * available: hay capacidad
        """
        zones = self

        # Defaults (cuando no hay FTTH instalado o sin datos)
        for z in zones:
            z.total_boxes = 0
            z.total_ports = 0
            z.used_ports = 0
            z.free_box_ports = 0
            z.free_subinterfaces = 0
            z.has_coverage = False
            z.coverage_status = 'no_coverage'

        valid_groups, zone_to_port_ids = self._get_valid_box_groups(zones)
        if not valid_groups:
            return

        # total_ports por zona (desde box_group.total_ports, stored=True)
        BoxGroup = valid_groups
        rg_ports = BoxGroup.read_group(
            domain=[('id', 'in', valid_groups.ids)],
            fields=['zone_id', 'total_ports'],
            groupby=['zone_id'],
            lazy=False,
        )
        total_ports_by_zone = {row['zone_id'][0]: (row.get('total_ports', 0) or 0) for row in rg_ports if row.get('zone_id')}

        # total_boxes por zona (sin dotted groupby)
        Box = self._get_ftth_model('wigo.ftth.box')
        total_boxes_by_zone = {}
        if Box is not None:
            group_to_zone = {g.id: g.zone_id.id for g in valid_groups if g.zone_id}

            rg_boxes = Box.read_group(
                domain=[('box_group_id', 'in', valid_groups.ids)],
                fields=['box_group_id'],
                groupby=['box_group_id'],
                lazy=False,
            )

            for row in rg_boxes:
                group = row.get('box_group_id')
                if not group:
                    continue
                group_id = group[0]
                zid = group_to_zone.get(group_id)
                if not zid:
                    continue
                total_boxes_by_zone[zid] = total_boxes_by_zone.get(zid, 0) + (row.get('__count', 0) or 0)

        # Puertos de caja libres/usados por zona
        free_box_ports_by_zone, used_ports_by_zone = self._get_free_box_ports(valid_groups)

        # Subinterfaces libres por zona (vía puertos OLT de box groups válidos)
        free_sub_by_zone = self._get_free_subinterfaces(zone_to_port_ids)

        # Aplicar por registro
        for zone in zones:
            zid = zone.id
            zone.total_ports = total_ports_by_zone.get(zid, 0)
            zone.total_boxes = total_boxes_by_zone.get(zid, 0)
            zone.used_ports = used_ports_by_zone.get(zid, 0)
            zone.free_box_ports = free_box_ports_by_zone.get(zid, 0)
            zone.free_subinterfaces = free_sub_by_zone.get(zid, 0)

            # Si no hay box groups válidos para la zona, no hay cobertura
            if zid not in zone_to_port_ids:
                zone.coverage_status = 'no_coverage'
                zone.has_coverage = False
                continue

            # Si no hay puertos en absoluto (ni declarados ni reales), no hay infraestructura útil
            if zone.total_ports <= 0 and (zone.used_ports + zone.free_box_ports) <= 0:
                zone.coverage_status = 'no_coverage'
                zone.has_coverage = False
                continue

            # Saturación end-to-end
            if zone.free_box_ports <= 0 or zone.free_subinterfaces <= 0:
                zone.coverage_status = 'saturated'
                zone.has_coverage = False
                continue

            # Ocupación (NAP) para warning
            occupancy = (zone.used_ports / zone.total_ports) if zone.total_ports else 0.0
            if occupancy >= 0.80:
                zone.coverage_status = 'warning'
            else:
                zone.coverage_status = 'available'

            zone.has_coverage = True

    # ==========================================================================
    # Public API
    # ==========================================================================

    def check_ftth_coverage(self):
        """Return a compact coverage snapshot for this zone."""
        self.ensure_one()
        return {
            'has_coverage': bool(self.has_coverage),
            'status': self.coverage_status,
            'free_box_ports': int(self.free_box_ports or 0),
            'free_subinterfaces': int(self.free_subinterfaces or 0),
        }


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    _WIGO_INSTALLATION_FIELDS = ('zona', 'direccion', 'ubicacion', 'coordenadas')

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

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        if not self.env.context.get('skip_lead_to_partner_sync'):
            leads._sync_wigo_installation_to_partner()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_lead_to_partner_sync'):
            return res

        if any(field in vals for field in self._WIGO_INSTALLATION_FIELDS) or 'partner_id' in vals:
            self._sync_wigo_installation_to_partner()
        return res

    def _sync_wigo_installation_to_partner(self):
        Lead = self.env['crm.lead']
        for lead in self:
            if not lead.partner_id:
                continue

            vals = {
                'zona': lead.zona or False,
                'direccion': lead.direccion or False,
                'ubicacion': lead.ubicacion or False,
                'coordenadas': lead.coordenadas or False,
            }

            lead.partner_id.with_context(skip_partner_to_lead_sync=True).write(vals)

            sibling_leads = Lead.search([
                ('partner_id', '=', lead.partner_id.id),
                ('id', '!=', lead.id),
            ])
            if sibling_leads:
                sibling_leads.with_context(skip_lead_to_partner_sync=True).write(vals)

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

