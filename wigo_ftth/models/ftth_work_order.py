# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class FtthWorkOrder(models.Model):
    _name = 'wigo.ftth.work.order'
    _description = 'Orden de Trabajo FTTH'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, id desc'
    _rec_name = 'name'

    # ==========================================================================
    # Basic Fields
    # ==========================================================================
    name = fields.Char(string='Referencia OT', readonly=True, copy=False, default='Nueva OT')

    work_type = fields.Selection([
        ('installation', 'Instalación'),
        ('deactivation', 'Baja / Retiro'),
    ], string='Tipo', required=True, default='installation', tracking=True)

    state = fields.Selection([
        ('pending', 'Pendiente de asignación'),
        ('assigned', 'Asignada'),
        ('in_field', 'En campo'),
        ('installed', 'Instalado — pend. configuración'),
        ('active', 'Configurado — Activo'),
        ('incident', 'Con incidencia'),
        ('deactivation_executed', 'Baja ejecutada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', default='pending', required=True, tracking=True)

    # ==========================================================================
    # Customer Data
    # ==========================================================================
    contract_id = fields.Many2one('customer.contract', string='Contrato', tracking=True)

    partner_id = fields.Many2one(related='contract_id.partner_id', store=True, readonly=True)
    plan_id = fields.Many2one(related='contract_id.plan_id', store=True, readonly=True)
    customer_code = fields.Char(related='contract_id.name', store=True, readonly=True)

    address = fields.Char(string='Dirección')
    location_link = fields.Char(string='Ubicación (Google Maps)', help='Enlace de Google Maps')
    reference_zone = fields.Char(string='Zona de referencia')
    contact_phone = fields.Char(string='Celular del cliente')

    lead_id = fields.Many2one('crm.lead', string='Lead origen', readonly=True)

    # ==========================================================================
    # Assignment
    # ==========================================================================
    installer_id = fields.Many2one('wigo.ftth.installer', string='Instalador asignado', tracking=True)
    technical_responsible_id = fields.Many2one('hr.employee', string='Responsable técnico')

    scheduled_date = fields.Datetime(string='Fecha/hora programada')
    execution_date = fields.Datetime(string='Fecha de ejecución')

    # ==========================================================================
    # Technical Route
    # ==========================================================================
    zone_id = fields.Many2one('wigo.zone', string='Zona', tracking=True)

    box_group_id = fields.Many2one(
        'wigo.ftth.box.group',
        string='Grupo de cajas',
        domain="[('zone_id', '=', zone_id)]",
        tracking=True,
    )

    node_id = fields.Many2one('wigo.ftth.nodo', string='Nodo')

    olt_id = fields.Many2one('wigo.ftth.olt', string='OLT', tracking=True)

    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto OLT',
        domain="[('olt_id', '=', olt_id)]",
    )

    odn_id = fields.Many2one('wigo.ftth.odn', string='ODN')

    box_id = fields.Many2one(
        'wigo.ftth.box',
        string='Caja',
        domain="[('box_group_id', '=', box_group_id)]",
    )

    box_port_id = fields.Many2one(
        'wigo.ftth.box.port',
        string='Puerto de caja',
        domain="[('box_id', '=', box_id), ('state', '=', 'occupied')]",
        tracking=True,
    )

    subinterface_id = fields.Many2one(
        'wigo.ftth.subinterface',
        string='Subinterfaz OLT',
        domain="[('olt_port_id', '=', olt_port_id), ('state', '=', 'occupied')]",
        tracking=True,
    )

    onu_id = fields.Many2one(
        'wigo.ftth.onu',
        string='ONU asignada',
        domain="[('state', '=', 'available')]",
        tracking=True,
    )

    # Datos de la ONU (solo lectura)
    onu_state = fields.Selection(related='onu_id.state', string='Estado ONU', readonly=True)
    onu_serial_number = fields.Char(related='onu_id.serial_number', string='Nº serie ONU', readonly=True)
    onu_rotulo = fields.Char(related='onu_id.rotulo', string='Rótulo / Etiqueta', readonly=True)
    onu_marca = fields.Char(related='onu_id.marca', string='Marca', readonly=True)
    onu_modelo = fields.Char(related='onu_id.modelo', string='Modelo', readonly=True)
    onu_perfil_olt = fields.Char(related='onu_id.perfil_olt', string='Perfil OLT', readonly=True)
    onu_pon_sn = fields.Char(related='onu_id.pon_sn', string='PON S/N', readonly=True)
    onu_wifi_ssid = fields.Char(related='onu_id.wifi_ssid', string='WiFi SSID', readonly=True)
    onu_wifi_password = fields.Char(
        related='onu_id.wifi_password',
        string='WiFi Password',
        readonly=True,
        groups='wigo_ftth.group_ftth_tech'
    )

    # ==========================================================================
    # Extras
    # ==========================================================================
    accessories = fields.Text(string='Accesorios entregados')
    notes = fields.Text(string='Observaciones')
    cancellation_reason = fields.Text(string='Motivo de cancelación', tracking=True)

    client_service_id = fields.Many2one(
        'wigo.ftth.client.service',
        string='Ficha técnica',
        readonly=True
    )

    # ==========================================================================
    # Create Override
    # ==========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Nueva OT':
                vals['name'] = sequence.next_by_code('wigo.ftth.work.order') or '/'
        return super().create(vals_list)

    # ==========================================================================
    # Onchange Methods
    # ==========================================================================
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            self._reset_contract_data()
            return

        self._load_contract_data(self.contract_id)

    def _reset_contract_data(self):
        self.customer_code = False
        self.partner_id = False
        self.plan_id = False
        self.address = False
        self.contact_phone = False
        self.location_link = False
        self.scheduled_date = False

    def _load_contract_data(self, contract):
        self.customer_code = contract.name
        self.partner_id = contract.partner_id.id
        self.plan_id = contract.plan_id.id
        self.address = contract.address
        self.contact_phone = contract.mobile
        self.location_link = contract.location_link
        self.scheduled_date = contract.installation_date
        self.lead_id = contract.lead_id.id if contract.lead_id else False

    @api.onchange('zone_id')
    def _onchange_zone_id(self):
        self._reset_technical_route()

    def _reset_technical_route(self):
        self.box_group_id = False
        self.olt_id = False
        self.olt_port_id = False
        self.odn_id = False
        self.node_id = False
        self.box_id = False
        self.box_port_id = False
        self.subinterface_id = False

    @api.onchange('box_group_id')
    def _onchange_box_group_id(self):
        self.box_id = False
        self.box_port_id = False
        self.subinterface_id = False

        if not self.box_group_id:
            self.olt_id = False
            self.olt_port_id = False
            self.odn_id = False
            self.node_id = False
            return

        self._load_group_data(self.box_group_id)

    def _load_group_data(self, group):
        if group.olt_port_id:
            self.olt_port_id = group.olt_port_id
            self.olt_id = group.olt_port_id.olt_id
            self.node_id = group.olt_port_id.olt_id.node_id if group.olt_port_id.olt_id else False
        else:
            self.olt_port_id = False
            self.olt_id = False
            self.node_id = False

        self.odn_id = group.odn_id if group.odn_id else False

    @api.onchange('box_id')
    def _onchange_box_id(self):
        self.box_port_id = False
        self.subinterface_id = False

    @api.onchange('box_port_id')
    def _onchange_box_port_id(self):
        self.subinterface_id = False

        if self.box_port_id:
            sub = self.box_port_id.subinterface_id
            # Si el puerto ya está vinculado a una subinterfaz, autocompletarla
            # (puede estar en infraestructura, asignada a OT, en activación o activa).
            if sub and sub.state != 'free':
                self.subinterface_id = sub

    # ==========================================================================
    # State Transitions
    # ==========================================================================
    def action_assign(self):
        for record in self:
            self._validate_assignment(record)

            record.write({'state': 'assigned'})

            # Recursos quedan "apartados" para esta OT
            if record.subinterface_id:
                record.subinterface_id.sudo().write({'state': 'allocated'})

            if record.box_port_id:
                record.box_port_id.sudo().write({'state': 'allocated'})

            if record.onu_id:
                record.onu_id.sudo().write({
                    'state': 'in_field',
                    'installer_id': record.installer_id.id
                })

    def _validate_assignment(self, record):
        if not record.onu_id:
            raise ValidationError("Debe asignar una ONU antes de pasar a Asignada.")
        if not record.subinterface_id:
            raise ValidationError("Debe asignar una subinterfaz OLT antes de pasar a Asignada.")
        if not record.installer_id:
            raise ValidationError("Debe asignar un instalador antes de pasar a Asignada.")

        # Disponibilidad de recursos
        if record.subinterface_id.state != 'occupied':
            raise ValidationError("La subinterfaz seleccionada no está disponible (debe estar en 'Infraestructura').")

        if record.box_port_id and record.box_port_id.state != 'occupied':
            raise ValidationError("El puerto de caja seleccionado no está disponible (debe estar en 'Infraestructura').")

    def action_in_field(self):
        for record in self:
            record.write({
                'state': 'in_field',
                'execution_date': fields.Datetime.now()
            })

    def action_installed(self):
        for record in self:
            record.write({'state': 'installed'})

            # En esta etapa el cliente ya está instalado pero falta configurar/activar
            if record.subinterface_id:
                record.subinterface_id.sudo().write({'state': 'reserved'})

            if record.box_port_id:
                record.box_port_id.sudo().write({'state': 'reserved'})

    def action_activate(self):
        for record in self:
            record.write({'state': 'active'})
            record._create_or_update_client_service()
            record._sync_resources_on_activation()

    def _sync_resources_on_activation(self):
        self.ensure_one()

        if self.subinterface_id:
            self.subinterface_id.sudo().write({'state': 'active'})

        if self.box_port_id:
            self.box_port_id.sudo().write({'state': 'active'})

        if self.onu_id:
            self.onu_id.sudo().write({
                'state': 'assigned',
                'fecha_asignacion': fields.Date.today()
            })

    def action_incident(self):
        self.write({'state': 'incident'})

    def action_execute_deactivation(self):
        for record in self:
            record._release_resources()
            record.write({'state': 'deactivation_executed'})

    def action_cancel(self):
        """Cancelar la OT y liberar los recursos asociados."""
        for record in self:
            record._release_resources_on_cancel()
            record.write({'state': 'cancelled'})

    def _release_resources_on_cancel(self):
        """Liberar subinterfaz, puerto de caja y ONU al cancelar la OT.

        A diferencia de una baja, aquí se devuelven los recursos a
        infraestructura sin afectar la ficha técnica (que no debería
        existir si la OT no llegó a activarse).
        """
        self.ensure_one()

        if self.subinterface_id:
            self.subinterface_id.sudo().write({
                'state': 'occupied',
                'client_service_id': False,
                'onu_id': False,
            })

        if self.box_port_id:
            self.box_port_id.sudo().write({'state': 'occupied'})

        if self.onu_id:
            self.onu_id.sudo().write({
                'state': 'available',
                'client_service_id': False,
                'subinterface_id': False,
                'installer_id': False,
            })

    def _release_resources(self):
        # Volver a estado de infraestructura (sin cliente), manteniendo el enlace
        # subinterface ⇄ box_port para no perder la topología.
        if self.subinterface_id:
            self.subinterface_id.sudo().write({
                'state': 'occupied',
                'client_service_id': False,
                'onu_id': False,
            })

        if self.box_port_id:
            # No limpiar subinterface_id; solo devolver a infraestructura
            self.box_port_id.sudo().write({'state': 'occupied'})

        if self.onu_id:
            self.onu_id.sudo().write({
                'state': 'available',
                'client_service_id': False,
                'subinterface_id': False,
                'installer_id': False,
            })

        if self.client_service_id:
            self.client_service_id.sudo().write({
                'estado_servicio': 'baja',
                'fecha_baja': fields.Date.today(),
            })

    # ==========================================================================
    # Client Service
    # ==========================================================================
    def _create_or_update_client_service(self):
        self.ensure_one()

        service_model = self.env['wigo.ftth.client.service'].sudo()

        domain = [('work_order_id', '=', self.id)]
        if self.lead_id:
            domain = ['|', ('lead_id', '=', self.lead_id.id), ('work_order_id', '=', self.id)]

        existing = service_model.search(domain, limit=1)

        vals = self._prepare_client_service_vals()

        if existing:
            # No reescribir datos históricos si ya existen.
            if existing.fecha_instalacion:
                vals.pop('fecha_instalacion', None)
            vals.pop('estado_servicio', None)

            existing.write(vals)
            service = existing
        else:
            service = service_model.create(vals)

        self.client_service_id = service.id
        self._link_resources_to_service(service)

    def _prepare_client_service_vals(self):
        # Importante: algunos campos de la ONU (p.ej. wifi_password) están restringidos por grupos.
        # Usamos sudo() para poder leerlos durante la activación aunque el usuario no sea técnico.
        onu = self.onu_id.sudo() if self.onu_id else False
        lead = self.lead_id.sudo() if self.lead_id else False
        sub = self.subinterface_id.sudo() if self.subinterface_id else False
        _logger.info(f"Preparando vals para ficha técnica desde OT {self.name} (ONU: {onu}, Subinterface: {sub.vlan_id})")
        return {
            'partner_id': self.partner_id.id,
            'codigo_cliente': self.customer_code,
            'plan_id': self.plan_id.id if self.plan_id else False,
            'servicio': self.plan_id.display_name if self.plan_id else False,
            'fecha_instalacion': fields.Date.today(),
            'estado_servicio': 'active',

            # Comercial (si hay lead de origen)
            'gestor_comercial': lead.team_id.name if lead and lead.team_id else False,
            'responsable_comercial_id': lead.user_id.id if lead and lead.user_id else False,

            # Topología / ruta
            'nodo_id': self.node_id.id if self.node_id else False,
            'olt_id': self.olt_id.id if self.olt_id else False,
            'olt_port_id': self.olt_port_id.id if self.olt_port_id else False,
            'subinterface_id': self.subinterface_id.id if self.subinterface_id else False,
            'odn_id': self.odn_id.id if self.odn_id else False,
            'box_group_id': self.box_group_id.id if self.box_group_id else False,
            'box_id': self.box_id.id if self.box_id else False,
            'box_port_id': self.box_port_id.id if self.box_port_id else False,

            # Equipos
            'onu_id': onu.id if onu else False,

            # Operación
            'installer_id': self.installer_id.id if self.installer_id else False,
            'link_ubicacion': self.location_link,
            'observaciones': self.notes or False,

            # Config / WiFi (si viene en la ONU seleccionada)
            'vlan': str(sub.vlan_id) if sub and sub.vlan_id else False,
            'tcont': onu.tcont if onu else False,
            'gemport': onu.gemport if onu else False,
            'vport': onu.vport if onu else False,
            'wifi_ssid': onu.wifi_ssid if onu else False,
            'wifi_pass': onu.wifi_password if onu else False,

            # Vínculos
            'lead_id': self.lead_id.id if self.lead_id else False,
            'work_order_id': self.id,
        }

    def _link_resources_to_service(self, service):
        if self.subinterface_id:
            self.subinterface_id.sudo().write({
                'client_service_id': service.id,
                'onu_id': self.onu_id.id if self.onu_id else False,
            })

        if self.onu_id:
            self.onu_id.sudo().write({
                'client_service_id': service.id,
                'subinterface_id': self.subinterface_id.id if self.subinterface_id else False,
            })

    def action_view_client_service(self):
        self.ensure_one()
        if not self.client_service_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Ficha Técnica',
            'res_model': 'wigo.ftth.client.service',
            'view_mode': 'form',
            'res_id': self.client_service_id.id,
        }