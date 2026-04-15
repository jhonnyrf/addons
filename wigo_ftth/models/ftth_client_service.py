# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FtthClientService(models.Model):
    _name = 'wigo.ftth.client.service'
    _description = 'Ficha Técnica del Cliente FTTH'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'codigo_cliente'
    _rec_name = 'codigo_cliente'

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

    # ── Topología de red (solo Técnica) ───────────────────────────
    nodo_id = fields.Many2one('wigo.ftth.nodo', string='Nodo', groups='wigo_ftth.group_ftth_tech')
    olt_id = fields.Many2one('wigo.ftth.olt', string='OLT', groups='wigo_ftth.group_ftth_tech')
    olt_port_id = fields.Many2one('wigo.ftth.olt.port', string='Puerto OLT', groups='wigo_ftth.group_ftth_tech')
    subinterface_id = fields.Many2one('wigo.ftth.subinterface', string='Subinterfaz OLT',
                                      groups='wigo_ftth.group_ftth_tech', tracking=True)
    odn_id = fields.Many2one('wigo.ftth.odn', string='ODN', groups='wigo_ftth.group_ftth_tech')
    box_group_id = fields.Many2one('wigo.ftth.box.group', string='Grupo de cajas',
                                   groups='wigo_ftth.group_ftth_tech')
    box_id = fields.Many2one('wigo.ftth.box', string='NAP', groups='wigo_ftth.group_ftth_tech')
    box_port_id = fields.Many2one('wigo.ftth.box.port', string='Puerto NAP',
                                  groups='wigo_ftth.group_ftth_tech')

    # ── ONU ───────────────────────────────────────────────────────
    onu_id = fields.Many2one('wigo.ftth.onu', string='ONU (N/S)',
                             groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')

    # ── Credenciales PPPoE / VLAN (solo Técnica) ──────────────────
    pppoe_user = fields.Char(string='Usuario PPPoE', groups='wigo_ftth.group_ftth_tech')
    pppoe_password = fields.Char(string='Contraseña PPPoE', groups='wigo_ftth.group_ftth_tech')
    vlan = fields.Char(string='VLAN', groups='wigo_ftth.group_ftth_tech')
    tcont = fields.Char(string='T-CONT', groups='wigo_ftth.group_ftth_tech')
    gemport = fields.Char(string='GEM Port', groups='wigo_ftth.group_ftth_tech')
    vport = fields.Char(string='V-Port', groups='wigo_ftth.group_ftth_tech')

    # ── WiFi (solo Técnica) ───────────────────────────────────────
    wifi_ssid = fields.Char(string='WiFi SSID', groups='wigo_ftth.group_ftth_tech')
    wifi_pass = fields.Char(string='WiFi Password', groups='wigo_ftth.group_ftth_tech')

    # ── Equipos adicionales (cámaras, routers, etc.) ─────────────
    equipo_adicional_1 = fields.Char(string='Equipo adicional 1',
                                     groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_1_marca = fields.Char(string='Marca eq. 1',
                                           groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_1_rotulo = fields.Char(string='Rótulo eq. 1',
                                            groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_1_sn = fields.Char(string='S/N eq. 1',
                                        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_2 = fields.Char(string='Equipo adicional 2',
                                     groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_2_marca = fields.Char(string='Marca eq. 2',
                                           groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_2_rotulo = fields.Char(string='Rótulo eq. 2',
                                            groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    equipo_adicional_2_sn = fields.Char(string='S/N eq. 2',
                                        groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')

    # ── Instalador ────────────────────────────────────────────────
    installer_id = fields.Many2one('wigo.ftth.installer', string='Técnico instalador',
                                   groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    ruta = fields.Char(string='Ruta (ODN → NAP → Puerto)', compute='_compute_ruta', store=True,
                       groups='wigo_ftth.group_ftth_tech')
    link_ubicacion = fields.Char(string='Ubicación (Google Maps)',
                                 groups='wigo_ftth.group_ftth_tech,wigo_ftth.group_ftth_readonly')
    observaciones = fields.Text(string='Observaciones', groups='wigo_ftth.group_ftth_tech')

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

    def action_view_work_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Trabajo',
            'res_model': 'wigo.ftth.work.order',
            'view_mode': 'form',
            'res_id': self.work_order_id.id,
        }
