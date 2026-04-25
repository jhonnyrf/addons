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

    def action_view_work_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Trabajo',
            'res_model': 'wigo.ftth.work.order',
            'view_mode': 'form',
            'res_id': self.work_order_id.id,
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
            if onu_field in onu_fields:
                onu_vals[onu_field] = self[service_field]
        return onu_vals

    def _sync_onu_configuration(self, trigger_vals=None):
        if self.env.context.get('skip_onu_sync'):
            return

        for record in self:
            if not record.onu_id:
                continue

            if trigger_vals is None or 'onu_id' in trigger_vals:
                onu_vals = record._get_onu_sync_vals()
            else:
                onu_vals = {}
                onu_fields = record.onu_id._fields
                for service_field, onu_field in record._ONU_SYNC_FIELD_MAP.items():
                    if service_field in trigger_vals and onu_field in onu_fields:
                        onu_vals[onu_field] = record[service_field]

            if onu_vals:
                record.onu_id.sudo().with_context(skip_onu_sync=True).write(onu_vals)
