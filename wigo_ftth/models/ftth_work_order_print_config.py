# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FtthWorkOrderPrintConfig(models.Model):
    _name = 'wigo.ftth.work.order.print.config'
    _description = 'Configuración Planilla PDF OT FTTH'

    name = fields.Char(default='Configuración Planilla OT FTTH', readonly=True)

    # Encabezado
    titulo_documento = fields.Char(string='Título documento', default='ORDEN DE TRABAJO FTTH')
    subtitulo_documento = fields.Char(string='Subtítulo', default='Planilla de instalación / baja')
    mostrar_numero_grande = fields.Boolean(string='Destacar número de OT', default=True)
    border_radius = fields.Integer(string='Redondez bordes (px)', default=0)

    # Empresa / contacto
    empresa_nombre = fields.Char(string='Nombre empresa', default='WIGO FAST')
    empresa_slogan = fields.Char(string='Slogan / leyenda', default='Tu internet veloz y confiable')
    empresa_direccion = fields.Char(string='Dirección')
    empresa_ciudad = fields.Char(string='Ciudad')
    empresa_telefono = fields.Char(string='Teléfono empresa')
    empresa_email = fields.Char(string='Email empresa')
    empresa_nit = fields.Char(string='NIT empresa')

    # Logo
    usar_logo_imagen = fields.Boolean(string='Usar logo imagen', default=True)
    layout_logo = fields.Selection([
        ('izquierda', 'Logo a la izquierda'),
        ('derecha', 'Logo a la derecha'),
        ('centrado', 'Logo centrado'),
    ], string='Posición del logo', default='izquierda')
    logo = fields.Binary(string='Logo del reporte')
    logo_fname = fields.Char(string='Nombre archivo logo')
    logo_ancho = fields.Integer(string='Ancho logo (px)', default=110)

    # QR Codes
    qr_cobranzas = fields.Binary(string='QR Número de Cobranzas')
    qr_cobranzas_fname = fields.Char(string='Nombre archivo QR Cobranzas')
    qr_soporte = fields.Binary(string='QR Número Atención/Soporte')
    qr_soporte_fname = fields.Char(string='Nombre archivo QR Soporte')

    # Firma / pie
    firma_nombre = fields.Char(string='Nombre firmante', default='Responsable Técnico')
    firma_cargo = fields.Char(string='Cargo', default='Área Técnica')
    firma_celular = fields.Char(string='CEL firmante')
    mostrar_pie = fields.Boolean(string='Mostrar pie de página', default=True)
    texto_pie = fields.Char(string='Texto pie de página', default='La información de esta OT es parte del control técnico.')

    # Colores
    color_primario = fields.Char(string='Color primario', default='#7a3f98')
    # Números de contacto
    numero_cobranzas = fields.Char(string='Número de Cobranzas', default='73802898')
    numero_soporte = fields.Char(string='Número Atención/Soporte', default='63888133')

    # Colores
    color_primario = fields.Char(string='Color primario', default='#7a3f98')
    color_secundario = fields.Char(string='Color secundario', default='#b564d6')
    color_texto_header = fields.Char(string='Color texto encabezado', default='#ffffff')
    color_borde = fields.Char(string='Color bordes', default='#cfcfd6')
    color_fondo = fields.Char(string='Color fondo', default='#ffffff')
    color_texto = fields.Char(string='Color texto', default='#1f1f1f')
    color_fondo_monto = fields.Char(string='Color fondo monto', default='#f6eef9')

    # Tipografía
    fuente_familia = fields.Selection([
        ('Arial, sans-serif', 'Arial'),
        ('Georgia, serif', 'Georgia'),
        ('Times New Roman, serif', 'Times New Roman'),
        ('Trebuchet MS, sans-serif', 'Trebuchet MS'),
        ('Verdana, sans-serif', 'Verdana'),
        ('Tahoma, sans-serif', 'Tahoma'),
    ], string='Fuente', default='Arial, sans-serif')
    tamano_fuente_base = fields.Integer(string='Tamaño base (px)', default=11)
    tamano_titulo = fields.Integer(string='Tamaño título (px)', default=18)
    tamano_empresa = fields.Integer(string='Tamaño empresa (px)', default=14)
    fuente_titulo_negrita = fields.Boolean(string='Título en negrita', default=True)

    # Layout / secciones
    mostrar_banda_decorativa = fields.Boolean(string='Mostrar banda decorativa', default=True)
    ancho_banda = fields.Integer(string='Ancho de banda (px)', default=8)
    mostrar_columna_codigo = fields.Boolean(string='Mostrar código de cliente', default=True)
    mostrar_equipos_instalados = fields.Boolean(string='Mostrar equipos instalados', default=True)
    mostrar_materiales = fields.Boolean(string='Mostrar materiales', default=True)
    mostrar_observaciones = fields.Boolean(string='Mostrar observaciones', default=True)
    mostrar_conformidad = fields.Boolean(string='Mostrar conformidad del cliente', default=True)

    # Tabla
    tabla_header_texto = fields.Char(string='Encabezado descripción', default='DESCRIPCIÓN')
    tabla_monto_texto = fields.Char(string='Encabezado monto', default='MONTO (Bs.)')

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
            'mostrar_numero_grande': True,
            'border_radius': 0,
            'empresa_nombre': 'WIGO FAST',
            'empresa_slogan': 'Tu internet veloz y confiable',
            'empresa_direccion': False,
            'empresa_ciudad': False,
            'empresa_telefono': False,
            'empresa_email': False,
            'empresa_nit': False,
            'usar_logo_imagen': True,
            'layout_logo': 'izquierda',
            'logo_ancho': 110,
            'firma_nombre': 'Responsable Técnico',
            'firma_cargo': 'Área Técnica',
            'firma_celular': False,
            'mostrar_pie': True,
            'texto_pie': 'La información de esta OT es parte del control técnico.',
            'color_primario': '#7a3f98',
                        'numero_cobranzas': '73802898',
                        'numero_soporte': '63888133',
            'color_secundario': '#b564d6',
            'color_texto_header': '#ffffff',
            'color_borde': '#cfcfd6',
            'color_fondo': '#ffffff',
            'color_texto': '#1f1f1f',
            'color_fondo_monto': '#f6eef9',
            'fuente_familia': 'Arial, sans-serif',
            'tamano_fuente_base': 11,
            'tamano_titulo': 18,
            'tamano_empresa': 14,
            'fuente_titulo_negrita': True,
            'mostrar_banda_decorativa': True,
            'ancho_banda': 8,
            'mostrar_columna_codigo': True,
            'mostrar_equipos_instalados': True,
            'mostrar_materiales': True,
            'mostrar_observaciones': True,
            'mostrar_conformidad': True,
            'tabla_header_texto': 'DESCRIPCIÓN',
            'tabla_monto_texto': 'MONTO (Bs.)',
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

    def _binary_to_b64(self, value):
        if not value:
            return ''
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    @api.model
    def get_config_dict(self):
        cfg = self.get_config()
        return {
            'titulo_documento': cfg.titulo_documento,
            'subtitulo_documento': cfg.subtitulo_documento,
            'mostrar_numero_grande': cfg.mostrar_numero_grande,
            'border_radius': cfg.border_radius,
            'empresa_nombre': cfg.empresa_nombre,
            'empresa_slogan': cfg.empresa_slogan or '',
            'empresa_direccion': cfg.empresa_direccion or '',
            'empresa_ciudad': cfg.empresa_ciudad or '',
            'empresa_telefono': cfg.empresa_telefono or '',
            'empresa_email': cfg.empresa_email or '',
            'empresa_nit': cfg.empresa_nit or '',
            'usar_logo_imagen': cfg.usar_logo_imagen,
            'layout_logo': cfg.layout_logo,
            'logo_base64': self._binary_to_b64(cfg.logo),
            'logo_ancho': cfg.logo_ancho or 110,
            'qr_cobranzas_base64': self._binary_to_b64(cfg.qr_cobranzas),
            'qr_soporte_base64': self._binary_to_b64(cfg.qr_soporte),
            'firma_nombre': cfg.firma_nombre,
            'firma_cargo': cfg.firma_cargo,
            'firma_celular': cfg.firma_celular or '',
            'mostrar_pie': cfg.mostrar_pie,
            'texto_pie': cfg.texto_pie or '',
            'color_primario': cfg.color_primario,
                        'numero_cobranzas': cfg.numero_cobranzas or '73802898',
                        'numero_soporte': cfg.numero_soporte or '63888133',
            'color_secundario': cfg.color_secundario,
            'color_texto_header': cfg.color_texto_header,
            'color_borde': cfg.color_borde,
            'color_fondo': cfg.color_fondo,
            'color_texto': cfg.color_texto,
            'color_fondo_monto': cfg.color_fondo_monto,
            'fuente_familia': cfg.fuente_familia,
            'tamano_fuente_base': cfg.tamano_fuente_base,
            'tamano_titulo': cfg.tamano_titulo,
            'tamano_empresa': cfg.tamano_empresa,
            'fuente_titulo_negrita': cfg.fuente_titulo_negrita,
            'mostrar_banda_decorativa': cfg.mostrar_banda_decorativa,
            'ancho_banda': cfg.ancho_banda,
            'mostrar_columna_codigo': cfg.mostrar_columna_codigo,
            'mostrar_equipos_instalados': cfg.mostrar_equipos_instalados,
            'mostrar_materiales': cfg.mostrar_materiales,
            'mostrar_observaciones': cfg.mostrar_observaciones,
            'mostrar_conformidad': cfg.mostrar_conformidad,
            'tabla_header_texto': cfg.tabla_header_texto,
            'tabla_monto_texto': cfg.tabla_monto_texto,
        }
