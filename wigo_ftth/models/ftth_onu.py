from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FtthOnu(models.Model):
    _name = 'wigo.ftth.onu'
    _description = 'ONU / ONT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'serial_number'
    _rec_name = 'serial_number'

    serial_number = fields.Char(string='Número de serie', required=True, copy=False, index=True, tracking=True)
    rotulo = fields.Char(string='Rótulo / Etiqueta', help='Etiqueta física pegada al equipo')
    marca_id = fields.Many2one('wigo.ftth.brand', string='Marca', ondelete='restrict', required=True)
    marca = fields.Char(string='Marca')
    modelo_id = fields.Many2one('wigo.ftth.model', string='Modelo', ondelete='restrict')
    modelo = fields.Char(string='Modelo')
    perfil_olt = fields.Char(string='Perfil OLT')

    @api.onchange('marca_id')
    def _onchange_marca_id(self):
        for r in self:
            if r.marca_id:
                r.marca = r.marca_id.name

    @api.onchange('modelo_id')
    def _onchange_modelo_id(self):
        for r in self:
            if r.modelo_id:
                r.modelo = r.modelo_id.name

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        for vals in vals_list:
            if vals.get('marca_id') and not vals.get('marca'):
                vals['marca'] = self.env['wigo.ftth.brand'].browse(vals['marca_id']).name
            if vals.get('modelo_id') and not vals.get('modelo'):
                vals['modelo'] = self.env['wigo.ftth.model'].browse(vals['modelo_id']).name
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('marca_id') and not vals.get('marca'):
            vals['marca'] = self.env['wigo.ftth.brand'].browse(vals['marca_id']).name
        if vals.get('modelo_id') and not vals.get('modelo'):
            vals['modelo'] = self.env['wigo.ftth.model'].browse(vals['modelo_id']).name
        return super().write(vals)

    # PON identifiers
    pon_sn = fields.Char(string='PON S/N', help='identifica el equipo en la red GPON')
    tcont = fields.Char(string='T-CONT', help='Asigna el ancho de banda a una ONU')
    gemport = fields.Char(string='GEM Port', help='canal lógico que transporta datos dentro de GPON')
    vport = fields.Char(string='V-Port', help='Se usa para asociar servicios')

    # Configuración WAN / PPPoE
    pppoe_user = fields.Char(string='Usuario PPPoE', tracking=True)
    pppoe_password = fields.Char(string='Contraseña PPPoE', tracking=True)
    vlan = fields.Char(string='VLAN', tracking=True,help='número que identifica el tipo de tráfico')

    # WiFi
    wifi_ssid = fields.Char(string='WiFi SSID')
    wifi_password = fields.Char(string='WiFi Password', groups='wigo_ftth.group_ftth_tech')

    # Puertos ETH
    eth_ports = fields.Char(string='ETH Ports (1-4)')

    # Gestión
    user_mgmt = fields.Char(string='User mgmt', groups='wigo_ftth.group_ftth_tech')
    password_mgmt = fields.Char(string='Password mgmt', groups='wigo_ftth.group_ftth_tech')

    state = fields.Selection([
        ('available',  'Disponible'),
        ('assigned',   'Asignado a cliente'),
        ('in_field',   'Entregado a instalador'),
        ('retired',    'Retirado'),
        ('damaged',    'Dañado'),
    ], string='Estado', default='available', required=True, tracking=True)

    client_service_id = fields.Many2one('wigo.ftth.client.service', string='Servicio asignado', readonly=True)
    subinterface_id = fields.Many2one('wigo.ftth.subinterface', string='Subinterfaz OLT', readonly=True)
    installer_id = fields.Many2one('wigo.ftth.installer', string='Instalador responsable')
    batch_id = fields.Many2one('wigo.ftth.onu.batch', string='Lote de entrega')
    fecha_asignacion = fields.Date(string='Fecha de asignación', readonly=True)
    notes = fields.Text(string='Notas')

    @api.constrains('serial_number')
    def _check_unique_serial(self):
        for r in self:
            dup = self.search([('serial_number', '=', r.serial_number), ('id', '!=', r.id)], limit=1)
            if dup:
                raise ValidationError(f"El número de serie '{r.serial_number}' ya existe (RN-03).")

    def action_retire(self):
        for r in self:
            r.write({'state': 'retired', 'client_service_id': False, 'subinterface_id': False})


class FtthOnuBatch(models.Model):
    """Lote de ONUs entregado al instalador con accesorios."""
    _name = 'wigo.ftth.onu.batch'
    _description = 'Lote de Entrega de ONUs'
    _inherit = ['mail.thread']
    _order = 'fecha_entrega desc'
    _rec_name = 'name'

    name = fields.Char(string='Referencia', required=True, default='Nuevo lote')
    fecha_entrega = fields.Date(string='Fecha de entrega', required=True, default=fields.Date.today)
    installer_id = fields.Many2one('wigo.ftth.installer', string='Instalador', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable (técnica)')
    onu_ids = fields.One2many('wigo.ftth.onu', 'batch_id', string='ONUs del lote')
    total_onus = fields.Integer(compute='_compute_totals', string='Total ONUs')
    onus_instaladas = fields.Integer(compute='_compute_totals', string='Instaladas')
    onus_pendientes = fields.Integer(compute='_compute_totals', string='Pendientes')

    # Accesorios por instalación (valores promedio del lote)
    cable_drop_m = fields.Float(string='Cable Drop (m)')
    conectores = fields.Integer(string='Conectores')
    tensores = fields.Integer(string='Tensores')
    grapas = fields.Integer(string='Grapas')
    roseta_acoplador = fields.Integer(string='Roseta + acoplador')
    patch_cord = fields.Integer(string='Patch cord')
    dispersion_m = fields.Float(string='Dispersión (m)')
    cinta = fields.Integer(string='Cinta')
    precintos = fields.Integer(string='Precintos')

    notes = fields.Text(string='Notas')

    @api.depends('onu_ids', 'onu_ids.state')
    def _compute_totals(self):
        for r in self:
            onus = r.onu_ids
            r.total_onus = len(onus)
            r.onus_instaladas = len(onus.filtered(lambda o: o.state == 'assigned'))
            r.onus_pendientes = len(onus.filtered(lambda o: o.state == 'in_field'))
