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

    # Text blocks and labels (configurable)
    titulo_datos_tecnicos = fields.Char(string='Título Datos Técnicos', default='DATOS TÉCNICOS DEL SERVICIO')
    titulo_equipos = fields.Char(string='Título Equipos', default='EQUIPOS INSTALADOS')
    titulo_materiales = fields.Char(string='Título Materiales', default='MATERIALES')
    titulo_observaciones = fields.Char(string='Título Observaciones', default='OBSERVACIONES')
    titulo_conformidad = fields.Char(string='Título Conformidad', default='CONFORMIDAD')

    texto_observaciones = fields.Text(string='Texto Observaciones', default='')
    texto_conformidad = fields.Text(string='Texto Conformidad', default='Declaro haber recibido el servicio y/o material descrito. Conforme.')

    titulo_cobranzas = fields.Char(string='Título Cobranzas', default='Para Pago de Facturas')
    texto_para_pago = fields.Char(string='Texto para pago', default='Para Pago de Facturas')
    titulo_soporte = fields.Char(string='Título Soporte', default='Para Soporte Técnico')
    texto_para_soporte = fields.Char(string='Texto para soporte', default='Para Soporte Técnico')

    # Labels y columnas
    label_servicio = fields.Char(string='Label Servicio', default='SERVICIO')
    label_razon_social = fields.Char(string='Label Razón Social', default='Razón Social')
    label_nombre = fields.Char(string='Label Nombre', default='Nombre')
    label_email = fields.Char(string='Label Email', default='email')
    label_celular = fields.Char(string='Label Celular', default='Celular')
    label_telefono = fields.Char(string='Label Teléfono', default='Teléfono')
    label_direccion = fields.Char(string='Label Dirección', default='Dirección')
    label_coordenadas = fields.Char(string='Label Coordenadas', default='Coordenadas')

    col_equipo = fields.Char(string='Columna Equipo', default='EQUIPO')
    col_marca = fields.Char(string='Columna Marca', default='MARCA')
    col_modelo = fields.Char(string='Columna Modelo', default='MODELO')
    col_nro_serie = fields.Char(string='Columna Nro Serie', default='NRO DE SERIE')
    col_nro_serie_pon = fields.Char(string='Columna Nro Serie PON', default='NRO DE SERIE (PON S/N)')

    # Additional blocks
    instrucciones_texto = fields.Text(string='Bloque Instrucciones', default='')
    texto_legal = fields.Text(string='Texto Legal', default='')

    # Toggles for optional sections
    mostrar_qr_cobranzas = fields.Boolean(string='Mostrar QR Cobranzas', default=True)
    mostrar_qr_soporte = fields.Boolean(string='Mostrar QR Soporte', default=True)
    mostrar_firma = fields.Boolean(string='Mostrar firma', default=True)
    mostrar_datos_tecnicos = fields.Boolean(string='Mostrar datos técnicos', default=True)
    mostrar_bloque_soporte = fields.Boolean(string='Mostrar bloque soporte', default=True)

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
            'titulo_datos_tecnicos': 'DATOS TÉCNICOS DEL SERVICIO',
            'titulo_equipos': 'EQUIPOS INSTALADOS',
            'titulo_materiales': 'MATERIALES',
            'titulo_observaciones': 'OBSERVACIONES',
            'titulo_conformidad': 'CONFORMIDAD',
            'texto_observaciones': False,
            'texto_conformidad': 'Declaro haber recibido el servicio y/o material descrito. Conforme.',
            'titulo_cobranzas': 'Para Pago de Facturas',
            'texto_para_pago': 'Para Pago de Facturas',
            'titulo_soporte': 'Para Soporte Técnico',
            'texto_para_soporte': 'Para Soporte Técnico',
            'label_servicio': 'SERVICIO',
            'label_razon_social': 'Razón Social',
            'label_nombre': 'Nombre',
            'label_email': 'email',
            'label_celular': 'Celular',
            'label_telefono': 'Teléfono',
            'label_direccion': 'Dirección',
            'label_coordenadas': 'Coordenadas',
            'col_equipo': 'EQUIPO',
            'col_marca': 'MARCA',
            'col_modelo': 'MODELO',
            'col_nro_serie': 'NRO DE SERIE',
            'col_nro_serie_pon': 'NRO DE SERIE (PON S/N)',
            'instrucciones_texto': False,
            'texto_legal': False,
            'mostrar_qr_cobranzas': True,
            'mostrar_qr_soporte': True,
            'mostrar_firma': True,
            'mostrar_datos_tecnicos': True,
            'mostrar_bloque_soporte': True,
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
            # Text blocks and labels
            'titulo_datos_tecnicos': cfg.titulo_datos_tecnicos or 'DATOS TÉCNICOS DEL SERVICIO',
            'titulo_equipos': cfg.titulo_equipos or 'EQUIPOS INSTALADOS',
            'titulo_materiales': cfg.titulo_materiales or 'MATERIALES',
            'titulo_observaciones': cfg.titulo_observaciones or 'OBSERVACIONES',
            'titulo_conformidad': cfg.titulo_conformidad or 'CONFORMIDAD',
            'texto_observaciones': cfg.texto_observaciones or '',
            'texto_conformidad': cfg.texto_conformidad or 'Declaro haber recibido el servicio y/o material descrito. Conforme.',
            'titulo_cobranzas': cfg.titulo_cobranzas or 'Para Pago de Facturas',
            'texto_para_pago': cfg.texto_para_pago or 'Para Pago de Facturas',
            'titulo_soporte': cfg.titulo_soporte or 'Para Soporte Técnico',
            'texto_para_soporte': cfg.texto_para_soporte or 'Para Soporte Técnico',
            # Labels
            'label_servicio': cfg.label_servicio or 'SERVICIO',
            'label_razon_social': cfg.label_razon_social or 'Razón Social',
            'label_nombre': cfg.label_nombre or 'Nombre',
            'label_email': cfg.label_email or 'email',
            'label_celular': cfg.label_celular or 'Celular',
            'label_telefono': cfg.label_telefono or 'Teléfono',
            'label_direccion': cfg.label_direccion or 'Dirección',
            'label_coordenadas': cfg.label_coordenadas or 'Coordenadas',
            # Columns
            'col_equipo': cfg.col_equipo or 'EQUIPO',
            'col_marca': cfg.col_marca or 'MARCA',
            'col_modelo': cfg.col_modelo or 'MODELO',
            'col_nro_serie': cfg.col_nro_serie or 'NRO DE SERIE',
            'col_nro_serie_pon': cfg.col_nro_serie_pon or 'NRO DE SERIE (PON S/N)',
            # Additional blocks
            'instrucciones_texto': cfg.instrucciones_texto or '',
            'texto_legal': cfg.texto_legal or '',
            # Toggles
            'mostrar_qr_cobranzas': cfg.mostrar_qr_cobranzas,
            'mostrar_qr_soporte': cfg.mostrar_qr_soporte,
            'mostrar_firma': cfg.mostrar_firma,
            'mostrar_datos_tecnicos': cfg.mostrar_datos_tecnicos,
            'mostrar_bloque_soporte': cfg.mostrar_bloque_soporte,
        }
