# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FtthClientService(models.Model):
    _name = 'wigo.ftth.client.service'
    _description = 'Ficha Técnica del Cliente FTTH'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'codigo_cliente'
    _rec_name = 'codigo_cliente'

    _ONU_SYNC_FIELD_MAP = {
        'pppoe_user': 'pppoe_user',
        'pppoe_password': 'pppoe_password',
        'vlan': 'vlan',
        'tcont': 'tcont',
        'gemport': 'gemport',
        'vport': 'vport',
        'wifi_ssid': 'wifi_ssid',
        'wifi_pass': 'wifi_password',
    }

    # ── Datos del cliente ─────────────────────────────────────────
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, ondelete='restrict', tracking=True)
    codigo_cliente = fields.Char(string='Código CF', required=True, copy=False, index=True, tracking=True)
    plan_id = fields.Many2one('internet.plan', string='Plan contratado', tracking=True)
    servicio = fields.Char(string='Tipo de servicio', help='Ej: Internet PPPoE + Wi Fi + 2 cámaras')
    fecha_instalacion = fields.Date(string='Fecha de instalación', tracking=True)
    fecha_baja = fields.Date(string='Fecha de baja')
    estado_servicio = fields.Selection([
        ('active',     'Activo'),
        ('suspended',  'Suspendido'),
        ('corte',      'En corte (mora)'),
        ('baja',       'Dado de baja'),
        ('cancelado',  'Cancelado'),
    ], string='Estado', default='active', required=True, tracking=True)
    metraje = fields.Float(string='Metraje de fibra (m)', help='Metros de cable de fibra instalados')

    # ── Gestión comercial ─────────────────────────────────────────
    gestor_comercial = fields.Char(string='Gestión / Comisión', help='Ej: ASISCORP, Neida')
    responsable_comercial_id = fields.Many2one('res.users', string='Responsable comercial')

    # ── Topología de red (Técnica + Solo lectura + Manager) ───────
    nodo_id = fields.Many2one(
        'wigo.ftth.nodo',
        string='Nodo',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    regional_id = fields.Many2one(
        'wigo.ftth.regional',
        string='Regional',
        compute='_compute_regional_id',
        store=True,
        index=True,
        help='Regional a la que pertenece el nodo de esta ficha técnica.',
    )
    olt_id = fields.Many2one(
        'wigo.ftth.olt',
        string='OLT',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    olt_port_id = fields.Many2one(
        'wigo.ftth.olt.port',
        string='Puerto OLT',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    subinterface_id = fields.Many2one(
        'wigo.ftth.subinterface',
        string='Subinterfaz OLT',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
        tracking=True,
    )
    odn_id = fields.Many2one(
        'wigo.ftth.odn',
        string='ODN',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    box_group_id = fields.Many2one(
        'wigo.ftth.box.group',
        string='Grupo de cajas',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    box_id = fields.Many2one(
        'wigo.ftth.box',
        string='NAP',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    box_port_id = fields.Many2one(
        'wigo.ftth.box.port',
        string='Puerto NAP',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )

    # ── ONU ───────────────────────────────────────────────────────
    onu_id = fields.Many2one(
        'wigo.ftth.onu',
        string='ONU (N/S)',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )

    # ── Datos de la ONU (solo lectura, related) ──────────────────
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
        groups='wigo_ftth.group_ftth_tech',
    )

    # ── Credenciales PPPoE / VLAN (Técnica + Manager) ────────────
    pppoe_user = fields.Char(string='Usuario PPPoE', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')
    pppoe_password = fields.Char(string='Contraseña PPPoE', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')
    vlan = fields.Char(string='VLAN', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')
    tcont = fields.Char(string='T-CONT', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')
    gemport = fields.Char(string='GEM Port', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')
    vport = fields.Char(string='V-Port', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')

    # ── WiFi (Técnica + Manager) ──────────────────────────────────
    wifi_ssid = fields.Char(string='WiFi SSID', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')
    wifi_pass = fields.Char(string='WiFi Password', groups='wigo_ftth.group_ftth_tech,base.group_erp_manager')

    # ── Equipos adicionales (cámaras, routers, etc.) ─────────────
    additional_equipment_ids = fields.One2many(
        'wigo.ftth.additional.equipment',
        'client_service_id',
        string='Equipos adicionales',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )   

    # ── Instalador ────────────────────────────────────────────────
    installer_id = fields.Many2one(
        'wigo.ftth.installer',
        string='Técnico instalador',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    ruta = fields.Char(
        string='Ruta (ODN → NAP → Puerto)',
        compute='_compute_ruta',
        store=True,
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    link_ubicacion = fields.Char(
        string='Ubicación (Google Maps)',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )
    observaciones = fields.Html(
        string='Observaciones',
        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly,base.group_erp_manager',
    )

    # ── Vínculos ──────────────────────────────────────────────────
    lead_id = fields.Many2one('crm.lead', string='Lead origen', readonly=True)
    work_order_id = fields.Many2one('wigo.ftth.work.order', string='OT origen', readonly=True)

    work_order_accessory_ids = fields.One2many(
        'ftth.work.order.accessory',
        compute='_compute_work_order_accessory_ids',
        string='Accesorios utilizados',
        readonly=True,
    )

    # ── Incidencias (integrado desde wigo_helpdesk) ─────────────
    incident_count = fields.Integer(
        string='Incidencias',
        compute='_compute_incident_data',
        store=False,
    )
    incident_summary_html = fields.Html(
        string='Incidencias relacionadas',
        compute='_compute_incident_data',
        store=False,
    )

    def _get_helpdesk_ticket_model(self):
        return self.env.registry.get('helpdesk.ticket') and self.env['helpdesk.ticket'] or False

    def _compute_incident_data(self):
        Ticket = self._get_helpdesk_ticket_model()
        if not Ticket:
            for record in self:
                record.incident_count = 0
                record.incident_summary_html = '<p class="text-muted mb-0">El módulo de incidencias no está disponible en esta base de datos.</p>'
            return

        grouped = {}
        if self.ids:
            for row in Ticket.search_read(
                [('ftth_service_id', 'in', self.ids)],
                ['ftth_service_id', 'name', 'title', 'stage_id', 'create_date'],
                order='create_date desc, id desc',
            ):
                service_id = row['ftth_service_id'] and row['ftth_service_id'][0]
                grouped.setdefault(service_id, []).append(row)

        for record in self:
            tickets = grouped.get(record.id, [])
            record.incident_count = len(tickets)
            if not tickets:
                record.incident_summary_html = '<p class="text-muted mb-0">No hay incidencias registradas para esta ficha técnica.</p>'
                continue

            items = []
            for ticket in tickets:
                number = ticket.get('name') or '/'
                title = ticket.get('title') or ''
                stage = ticket.get('stage_id') and ticket['stage_id'][1] or ''
                created = ticket.get('create_date') or ''
                items.append(f'<li><strong>{number}</strong> — {title} <span class="text-muted">({stage})</span> <span class="text-muted">{created}</span></li>')
            record.incident_summary_html = '<ul class="mb-0">' + ''.join(items) + '</ul>'

    def _compute_ruta(self):
        for r in self:
            partes = []
            if r.odn_id:
                partes.append(r.odn_id.name)
            if r.box_id:
                partes.append(f'NAP {r.box_id.identificador}')
            if r.box_port_id:
                partes.append(f'P{r.box_port_id.numero_puerto}')
            r.ruta = ' → '.join(partes) if partes else ''

    @api.depends('nodo_id')
    def _compute_regional_id(self):
        for record in self:
            record.regional_id = record.nodo_id.regional_id if record.nodo_id else False

    def action_sync_from_work_order(self):
        """Actualizar la ficha técnica con la información que exista en la OT origen.

        Útil para fichas creadas antes de cambios de mapeo (o cuando se completan datos
        técnicos después de la activación).
        """
        self.ensure_one()
        if not self.work_order_id:
            return True

        vals = self.work_order_id.sudo()._prepare_client_service_vals()

        # Evitar sobre-escribir datos históricos/estado ya gestionado en la ficha.
        vals.pop('fecha_instalacion', None)
        vals.pop('estado_servicio', None)

        # No sobrescribir datos existentes con valores vacíos/nulos.
        # Este botón debe complementar información, no borrar contenido previo.
        cleaned_vals = {}
        for field_name, incoming_value in vals.items():
            current_value = self[field_name]
            if incoming_value in (False, None, ''):
                # Si ya hay dato en la ficha, preservar lo existente.
                if current_value not in (False, None, ''):
                    continue
                # Si ambos están vacíos, no hace falta escribir.
                continue
            cleaned_vals[field_name] = incoming_value

        if cleaned_vals:
            self.sudo().write(cleaned_vals)
        return True

    def _compute_work_order_accessory_ids(self):
        for record in self:
            record.work_order_accessory_ids = record.work_order_id.work_order_accessories if record.work_order_id else False

    def action_view_work_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Trabajo',
            'res_model': 'wigo.ftth.work.order',
            'view_mode': 'form',
            'res_id': self.work_order_id.id,
        }

    def action_register_incident(self):
        """Open a new Helpdesk ticket form prefilled with this ficha técnica data."""
        self.ensure_one()
        Ticket = self._get_helpdesk_ticket_model()
        if not Ticket:
            raise ValidationError('No se puede registrar una incidencia porque el módulo de Helpdesk no está instalado.')
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Registrar Incidencia',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ftth_service_id': self.id,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_customer_code': self.codigo_cliente or False,
                'default_customer_name': self.partner_id.name if self.partner_id else False,
                'default_customer_phone': self.partner_id.mobile if self.partner_id else False,
                'default_customer_address': self.link_ubicacion or False,
            },
        }
        return action

    def action_view_incidents(self):
        self.ensure_one()
        Ticket = self._get_helpdesk_ticket_model()
        if not Ticket:
            raise ValidationError('No se pueden visualizar incidencias porque el módulo de Helpdesk no está instalado.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incidencias relacionadas',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form,kanban',
            'domain': [('ftth_service_id', '=', self.id)],
            'context': {'default_ftth_service_id': self.id, 'default_partner_id': self.partner_id.id if self.partner_id else False},
        }

    def action_create_deactivation_work_order(self):
        """Crear una Orden de Trabajo de tipo Baja/Retiro desde la ficha técnica.

        El OT resultante tendrá `work_type='deactivation'`, no contendrá accesorios ni
        fecha programada, y no llevará instalador ni responsable técnico.
        """
        self.ensure_one()
        wo_model = self.env['wigo.ftth.work.order']

        # Try to find an active contract for this partner so related fields populate
        contract = self.env['customer.contract'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'active')
        ], limit=1)

        # Fill contact phone using partner data (independent field on WO)
        partner_phone = False
        if self.partner_id:
            partner_phone = self.partner_id.phone or False

        vals = {
            'work_type': 'deactivation',
            'contract_id': contract.id if contract else False,
            'customer_code': contract.name if contract else (self.codigo_cliente or False),
            'address': self.link_ubicacion or False,
            'location_link': self.link_ubicacion or False,
            'node_id': self.nodo_id.id if self.nodo_id else False,
            'olt_id': self.olt_id.id if self.olt_id else False,
            'olt_port_id': self.olt_port_id.id if self.olt_port_id else False,
            'subinterface_id': self.subinterface_id.id if self.subinterface_id else False,
            'odn_id': self.odn_id.id if self.odn_id else False,
            'box_group_id': self.box_group_id.id if self.box_group_id else False,
            'box_id': self.box_id.id if self.box_id else False,
            'box_port_id': self.box_port_id.id if self.box_port_id else False,
            'onu_id': self.onu_id.id if self.onu_id else False,
            'notes': self.observaciones or False,
            'client_service_id': self.id,
        }

        if partner_phone:
            vals['contact_phone'] = partner_phone

        # Create with explicit context flag to allow deactivation creation
        # Use skip_onu_sync to avoid triggering ONU sync during write
        wo = wo_model.with_context(allow_deactivation_create=True).create(vals)

        # Link back the created OT using skip_onu_sync context to avoid unnecessary sync
        self.with_context(skip_onu_sync=True).write({'work_order_id': wo.id})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Trabajo Baja',
            'res_model': 'wigo.ftth.work.order',
            'view_mode': 'form',
            'res_id': wo.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('install_mode') and not self.env.context.get('allow_ftth_cs_autocreate'):
            raise ValidationError(
                'No está permitido crear fichas técnicas manualmente. '
                'La ficha técnica se genera automáticamente desde la Orden de Trabajo de instalación.'
            )

        for vals in vals_list:
            if not vals.get('work_order_id') and not self.env.context.get('install_mode'):
                raise ValidationError(
                    'La ficha técnica debe estar vinculada a una Orden de Trabajo de instalación.'
                )

        services = super().create(vals_list)
        services._sync_onu_configuration()
        return services

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_onu_sync'):
            self._sync_onu_configuration(trigger_vals=vals)
        return res

    def _get_onu_sync_vals(self):
        self.ensure_one()
        if not self.onu_id:
            return {}

        onu_vals = {}
        onu_fields = self.onu_id._fields
        for service_field, onu_field in self._ONU_SYNC_FIELD_MAP.items():
            if service_field in self._fields and onu_field in onu_fields:
                onu_vals[onu_field] = self[service_field]
        return onu_vals

    def _sync_onu_configuration(self, trigger_vals=None):
        """Sincroniza campos de configuración de ONU cuando se actualiza la ficha técnica."""
        for record in self:
            if not record.onu_id:
                continue

            if trigger_vals:
                # Sync only the fields that were modified and exist in the mapping
                onu_vals = {}
                onu_fields = record.onu_id._fields
                for service_field, onu_field in record._ONU_SYNC_FIELD_MAP.items():
                    if service_field in trigger_vals and onu_field in onu_fields:
                        onu_vals[onu_field] = record[service_field]

                if onu_vals:
                    record.onu_id.sudo().with_context(skip_onu_sync=True).write(onu_vals)
            else:
                # Sync all mapped fields
                onu_vals = record._get_onu_sync_vals()
                if onu_vals:
                    record.onu_id.sudo().with_context(skip_onu_sync=True).write(onu_vals)
