# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FtthWorkOrderPrintConfig(models.Model):
    _name = 'wigo.ftth.work.order.print.config'
    _description = 'Configuración Planilla PDF OT FTTH'

    name = fields.Char(default='Configuración Planilla OT FTTH', readonly=True)

    # Encabezado
    titulo_documento = fields.Char(string='Título documento', default='ORDEN DE TRABAJO FTTH')
    subtitulo_documento = fields.Char(string='Subtítulo', default='Planilla de instalación / baja')

    # Empresa / contacto
    empresa_nombre = fields.Char(string='Nombre empresa', default='WIGO FAST')
    empresa_direccion = fields.Char(string='Dirección')
    empresa_ciudad = fields.Char(string='Ciudad')
    empresa_telefono = fields.Char(string='Teléfono empresa')
    empresa_email = fields.Char(string='Email empresa')

    # Logo
    usar_logo_imagen = fields.Boolean(string='Usar logo imagen', default=True)
    logo = fields.Binary(string='Logo del reporte')
    logo_fname = fields.Char(string='Nombre archivo logo')
    logo_ancho = fields.Integer(string='Ancho logo (px)', default=110)

    # QR Codes
    qr_cobranzas = fields.Binary(string='QR Número de Cobranzas')
    qr_cobranzas_fname = fields.Char(string='Nombre archivo QR Cobranzas')
    qr_soporte = fields.Binary(string='QR Número Atención/Soporte')
    qr_soporte_fname = fields.Char(string='Nombre archivo QR Soporte')

    # Firma
    firma_nombre = fields.Char(string='Nombre firmante', default='Responsable Técnico')
    firma_cargo = fields.Char(string='Cargo', default='Área Técnica')

    # Colores
    color_primario = fields.Char(string='Color primario', default='#7a3f98')
    color_secundario = fields.Char(string='Color secundario', default='#b564d6')
    color_texto_header = fields.Char(string='Color texto encabezado', default='#ffffff')
    color_borde = fields.Char(string='Color bordes', default='#cfcfd6')
    color_fondo = fields.Char(string='Color fondo', default='#ffffff')
    color_texto = fields.Char(string='Color texto', default='#1f1f1f')

    # Tipografía
    fuente_familia = fields.Selection([
        ('Arial, sans-serif', 'Arial'),
        ('Georgia, serif', 'Georgia'),
        ('Times New Roman, serif', 'Times New Roman'),
        ('Trebuchet MS, sans-serif', 'Trebuchet MS'),
        ('Verdana, sans-serif', 'Verdana'),
    ], string='Fuente', default='Arial, sans-serif')
    tamano_fuente_base = fields.Integer(string='Tamaño base (px)', default=11)
    tamano_titulo = fields.Integer(string='Tamaño título (px)', default=18)

    # Secciones
    mostrar_accesorios = fields.Boolean(string='Mostrar tabla de accesorios', default=True)
    mostrar_observaciones = fields.Boolean(string='Mostrar observaciones', default=True)

    @api.model
    def get_config(self):
        cfg = self.search([], limit=1)
        if not cfg:
            cfg = self.create({})
        return cfg

    def action_reset_defaults(self):
        self.ensure_one()
        self.write({
            'titulo_documento': 'ORDEN DE TRABAJO FTTH',
            'subtitulo_documento': 'Planilla de instalación / baja',
            'empresa_nombre': 'WIGO FAST',
            'empresa_direccion': False,
            'empresa_ciudad': False,
            'empresa_telefono': False,
            'empresa_email': False,
            'usar_logo_imagen': True,
            'logo_ancho': 110,
            'firma_nombre': 'Responsable Técnico',
            'firma_cargo': 'Área Técnica',
            'color_primario': '#7a3f98',
            'color_secundario': '#b564d6',
            'color_texto_header': '#ffffff',
            'color_borde': '#cfcfd6',
            'color_fondo': '#ffffff',
            'color_texto': '#1f1f1f',
            'fuente_familia': 'Arial, sans-serif',
            'tamano_fuente_base': 11,
            'tamano_titulo': 18,
            'mostrar_accesorios': True,
            'mostrar_observaciones': True,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Diseño restaurado',
                'message': 'Se restauraron los valores predeterminados de la planilla OT.',
                'sticky': False,
                'type': 'success',
            }
        }

    @api.model
    def get_config_dict(self):
        cfg = self.get_config()
        logo_b64 = False
        if cfg.logo:
            logo_b64 = cfg.logo.decode('utf-8') if isinstance(cfg.logo, bytes) else cfg.logo

        return {
            'titulo_documento': cfg.titulo_documento,
            'subtitulo_documento': cfg.subtitulo_documento,
            'empresa_nombre': cfg.empresa_nombre,
            'empresa_direccion': cfg.empresa_direccion or '',
            'empresa_ciudad': cfg.empresa_ciudad or '',
            'empresa_telefono': cfg.empresa_telefono or '',
            'empresa_email': cfg.empresa_email or '',
            'usar_logo_imagen': cfg.usar_logo_imagen,
            'logo_base64': logo_b64 or '',
            'logo_ancho': cfg.logo_ancho or 110,
            'firma_nombre': cfg.firma_nombre,
            'firma_cargo': cfg.firma_cargo,
            'color_primario': cfg.color_primario,
            'color_secundario': cfg.color_secundario,
            'color_texto_header': cfg.color_texto_header,
            'color_borde': cfg.color_borde,
            'color_fondo': cfg.color_fondo,
            'color_texto': cfg.color_texto,
            'fuente_familia': cfg.fuente_familia,
            'tamano_fuente_base': cfg.tamano_fuente_base,
            'tamano_titulo': cfg.tamano_titulo,
            'mostrar_accesorios': cfg.mostrar_accesorios,
            'mostrar_observaciones': cfg.mostrar_observaciones,
        }
