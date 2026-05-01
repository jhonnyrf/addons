from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import logging
_logger = logging.getLogger(__name__)


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

    telefono_contacto = fields.Char(
        string="Teléfono",
        compute='_compute_telefono_contacto',
        inverse='_inverse_telefono_contacto',
        readonly=False,
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
    contract_payment_mode = fields.Selection(
        selection=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('one_time', 'One Time'),
        ],
        string="Payment Mode",
        help="Select the payment mode for the contract.",
    )
    contract_payment_mode_display = fields.Char(
        related='contract_id.payment_mode',
        string="Payment Mode Display",
        store=False,
    )
    
    def _get_payment_mode_badge(self):
        for lead in self:
            if lead.contract_id:
                lead.contract_payment_mode = lead.contract_id.payment_mode
            else:
                lead.contract_payment_mode = False

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        self._get_payment_mode_badge()

    def action_view_contract(self):
        """Override to include payment mode in the contract view."""
        action = super(CrmLead, self).action_view_contract()
        if self.contract_id:
            action['context'] = {
                'default_payment_mode': self.contract_payment_mode,
            }
        return action

    def _compute_contract_count(self):
        for lead in self:
            lead.contract_count = 1 if lead.contract_id else 0
            lead.contract_payment_mode = lead.contract_id.payment_mode if lead.contract_id else False
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

    stage_show_button_won = fields.Boolean(
        related='stage_id.show_button_won',
        string="Mostrar botón ganado",
        readonly=True,
        store=True,
    )

    stage_show_button_lost = fields.Boolean(
        related='stage_id.show_button_lost',
        string="Mostrar botón perdido",
        readonly=True,
        store=True,
    )

    stage_show_button_new_contract = fields.Boolean(
        related='stage_id.show_button_new_contract',
        string="Mostrar botón nuevo contrato",
        readonly=True,
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

    @api.depends('partner_id')
    def _compute_telefono_contacto(self):
        for lead in self:
            partner = lead.partner_id
            if not partner:
                lead.telefono_contacto = False
                continue
            if 'celular' in partner._fields:
                lead.telefono_contacto = partner.celular or False
            else:
                lead.telefono_contacto = partner.phone or False

    @api.onchange('partner_id')
<<<<<<< HEAD
    def _onchange_partner_id_fill_installation_fields(self):
        for lead in self:
            partner = lead.partner_id
            if not partner:
                continue

            if not lead.zona:
                lead.zona = partner.zona or False
            if not lead.direccion:
                lead.direccion = partner.direccion or False
            if not lead.ubicacion:
                lead.ubicacion = partner.ubicacion or False
            if not lead.coordenadas:
                lead.coordenadas = partner.coordenadas or False
=======
    def _onchange_partner_id_sync_installation(self):
        """Al seleccionar un `partner` en el lead, traer los datos de
        instalación y plan si el lead no los tiene ya.
        """
        for lead in self:
            partner = lead.partner_id
            if not partner:
                _logger.debug("wigo_crm: onchange partner_id - no partner for lead %s", lead.id or '(new)')
                continue

            _logger.debug(
                "wigo_crm: onchange partner_id - lead=%s partner=%s (zona=%s direccion=%s ubicacion=%s coordenadas=%s)",
                lead.id or '(new)', partner.id, getattr(partner, 'zona', None), getattr(partner, 'direccion', None), getattr(partner, 'ubicacion', None), getattr(partner, 'coordenadas', None)
            )

            # Campos de instalación: solo rellenar si el lead no tiene valor
            if not lead.zona:
                if getattr(partner, 'zona', False):
                    lead.zona = partner.zona
                elif getattr(partner, 'zona_id', False):
                    # Fallback: usar nombre de zona relacionada
                    lead.zona = partner.zona_id.name
            if not lead.direccion and getattr(partner, 'direccion', False):
                lead.direccion = partner.direccion
            if not lead.ubicacion and getattr(partner, 'ubicacion', False):
                lead.ubicacion = partner.ubicacion
            if not lead.coordenadas and getattr(partner, 'coordenadas', False):
                lead.coordenadas = partner.coordenadas

            # Si no hay plan en el lead, intentar tomar el primer plan activo del partner
            try:
                plans = partner.partner_plan_ids.filtered(lambda p: p.state == 'active')
            except Exception:
                plans = partner.partner_plan_ids if partner.partner_plan_ids else self.env['partner.plan']

            if not lead.plan_id and plans:
                plan = plans[0]
                if plan.plan_id:
                    lead.plan_id = plan.plan_id.id
                if not lead.codigo_cliente and getattr(plan, 'codigo_cliente', False):
                    lead.codigo_cliente = plan.codigo_cliente

            _logger.debug("wigo_crm: onchange partner_id - after copy lead.zona=%s lead.direccion=%s", lead.zona, lead.direccion)
>>>>>>> 22bdc0b8f617fe06642d07818cd8c7c505b753ce

    def _inverse_telefono_contacto(self):
        for lead in self:
            partner = lead.partner_id
            if not partner:
                continue
            if 'celular' in partner._fields:
                partner.with_context(skip_partner_to_lead_sync=True).write({
                    'celular': lead.telefono_contacto or False,
                })
            else:
                partner.with_context(skip_partner_to_lead_sync=True).write({
                    'phone': lead.telefono_contacto or False,
                })

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

            vals = {}
            for field in self._WIGO_INSTALLATION_FIELDS:
                value = getattr(lead, field)
                if value:
                    vals[field] = value

            if not vals:
                continue

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

    def action_mark_won_wigo(self):
        """Método personalizado Wigo para marcar lead como ganado (Botón controlado por stage)"""
        return self.action_set_won_rainbowman()


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

