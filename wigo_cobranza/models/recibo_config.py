# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WigoReciboConfig(models.Model):
    """
    Configuración visual del recibo de cobranza.
    Singleton. Permite editar logo, datos, firma y diseño completo
    (colores, fuentes, tamaños, layout) desde la interfaz.
    """
    _name = 'wigo.recibo.config'
    _description = 'Configuración del Recibo de Cobro'

    name = fields.Char(default='Configuración del Recibo', readonly=True)

    # ── Empresa ──────────────────────────────────────────────────
    empresa_nombre = fields.Char(string='Nombre empresa', default='WIGO FAST')
    empresa_direccion = fields.Char(string='Dirección', default='Calle Junin Nº 425')
    empresa_ciudad = fields.Char(string='Ciudad', default='Cochabamba')
    empresa_celular = fields.Char(string='CEL empresa', default='63888133')
    empresa_email = fields.Char(string='Email empresa')
    empresa_nit = fields.Char(string='NIT')
    empresa_slogan = fields.Char(string='Slogan / tagline',
        help='Texto opcional debajo del nombre. Ej: "Tu internet veloz y confiable"')

    # ── Logo ─────────────────────────────────────────────────────
    logo = fields.Binary(string='Logo del recibo',
        help='Recomendado: fondo transparente, aprox. 300×120 px.')
    logo_fname = fields.Char(string='Nombre del archivo logo')
    usar_logo_imagen = fields.Boolean(string='Usar logo imagen', default=True)
    logo_ancho = fields.Integer(string='Ancho del logo (px)', default=90)

    # ── Firma ────────────────────────────────────────────────────
    firma_nombre = fields.Char(string='Nombre firmante', default='Lic. Patricia Villarroel')
    firma_cargo = fields.Char(string='Cargo', default='CONTABILIDAD')
    firma_celular = fields.Char(string='CEL firmante', default='68582771')

    # ── Pie de página ────────────────────────────────────────────
    texto_pie = fields.Char(string='Texto pie de página', default='Gracias por su pago puntual.')
    mostrar_pie = fields.Boolean(string='Mostrar pie de página', default=True)

    # ══ DISEÑO — Colores ═════════════════════════════════════════
    color_primario = fields.Char(string='Color primario', default='#cc0000',
        help='Encabezado de tabla, banda decorativa y acentos. Formato HEX.')
    color_secundario = fields.Char(string='Color secundario', default='#990000',
        help='Usado en degradado del header. Formato HEX.')
    color_texto_header = fields.Char(string='Color texto encabezado', default='#ffffff')
    color_fondo_recibo = fields.Char(string='Color fondo del recibo', default='#ffffff')
    color_texto_principal = fields.Char(string='Color texto principal', default='#222222')
    color_texto_secundario = fields.Char(string='Color texto secundario', default='#666666')
    color_borde = fields.Char(string='Color de bordes', default='#cccccc')
    color_fondo_monto = fields.Char(string='Color fondo del monto en letras', default='#f9f9f9')

    # ══ DISEÑO — Tipografía ══════════════════════════════════════
    fuente_familia = fields.Selection([
        ('Arial, sans-serif', 'Arial'),
        ('Georgia, serif', 'Georgia'),
        ('Times New Roman, serif', 'Times New Roman'),
        ('Courier New, monospace', 'Courier New'),
        ('Trebuchet MS, sans-serif', 'Trebuchet MS'),
        ('Verdana, sans-serif', 'Verdana'),
        ('Tahoma, sans-serif', 'Tahoma'),
    ], string='Fuente del recibo', default='Arial, sans-serif')
    tamano_fuente_base = fields.Integer(string='Tamaño fuente base (px)', default=12)
    tamano_titulo = fields.Integer(string='Tamaño título (px)', default=22)
    tamano_empresa = fields.Integer(string='Tamaño nombre empresa (px)', default=14)
    fuente_titulo_negrita = fields.Boolean(string='Título en negrita', default=True)

    # ══ DISEÑO — Layout / Estructura ═════════════════════════════
    estilo_header = fields.Selection([
        ('gradiente', 'Gradiente (degradado)'),
        ('solido', 'Color sólido'),
        ('linea', 'Solo línea inferior'),
        ('sin_fondo', 'Sin fondo (texto negro)'),
    ], string='Estilo del encabezado', default='gradiente')
    mostrar_banda_decorativa = fields.Boolean(string='Mostrar banda decorativa', default=True)
    ancho_banda = fields.Integer(string='Altura banda decorativa (px)', default=8)
    border_radius = fields.Integer(string='Redondez bordes (px)', default=0,
        help='0 = esquinas rectas. Valores mayores = más redondeado.')
    mostrar_numero_grande = fields.Boolean(string='Destacar número de recibo en grande', default=True)
    layout_logo = fields.Selection([
        ('derecha', 'Logo a la derecha'),
        ('izquierda', 'Logo a la izquierda'),
        ('centrado', 'Logo centrado (encima del nombre)'),
    ], string='Posición del logo', default='derecha')

    # ══ DISEÑO — Tabla de detalle ═════════════════════════════════
    tabla_header_texto = fields.Char(string='Encabezado col. descripción', default='DESCRIPCIÓN')
    tabla_monto_texto = fields.Char(string='Encabezado col. monto', default='MONTO (Bs.)')
    mostrar_columna_codigo = fields.Boolean(string='Mostrar código de cliente en tabla', default=True)

    @api.model
    def get_config(self):
        """Retorna el singleton de configuración, creándolo si no existe."""
        config = self.search([], limit=1)
        if not config:
            config = self.create({})
        return config

    def action_reset_defaults(self):
        """Restaura valores predeterminados de diseño."""
        self.ensure_one()
        self.write({
            'color_primario': '#cc0000', 'color_secundario': '#990000',
            'color_texto_header': '#ffffff', 'color_fondo_recibo': '#ffffff',
            'color_texto_principal': '#222222', 'color_texto_secundario': '#666666',
            'color_borde': '#cccccc', 'color_fondo_monto': '#f9f9f9',
            'fuente_familia': 'Arial, sans-serif', 'tamano_fuente_base': 12,
            'tamano_titulo': 22, 'tamano_empresa': 14, 'fuente_titulo_negrita': True,
            'estilo_header': 'gradiente', 'mostrar_banda_decorativa': True,
            'ancho_banda': 8, 'border_radius': 0, 'mostrar_numero_grande': True,
            'layout_logo': 'derecha',
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Diseño restaurado',
                'message': 'Se restauraron los valores predeterminados de diseño.',
                'sticky': False, 'type': 'success',
            }
        }

    @api.model
    def get_config_dict(self):
        """
        Retorna la configuración como dict JSON-serializable para el widget JS.
        Incluye logo en base64 si existe.
        """
        cfg = self.get_config()
        logo_b64 = False
        if cfg.logo:
            logo_b64 = cfg.logo.decode('utf-8') if isinstance(cfg.logo, bytes) else cfg.logo

        return {
            'empresa_nombre': cfg.empresa_nombre,
            'empresa_direccion': cfg.empresa_direccion,
            'empresa_ciudad': cfg.empresa_ciudad,
            'empresa_celular': cfg.empresa_celular,
            'empresa_email': cfg.empresa_email or '',
            'empresa_nit': cfg.empresa_nit or '',
            'empresa_slogan': cfg.empresa_slogan or '',
            'logo_base64': logo_b64 or '',
            'logo_ancho': cfg.logo_ancho or 90,
            'firma_nombre': cfg.firma_nombre,
            'firma_cargo': cfg.firma_cargo,
            'firma_celular': cfg.firma_celular,
            'texto_pie': cfg.texto_pie or '',
            'mostrar_pie': cfg.mostrar_pie,
            # colores
            'color_primario': cfg.color_primario,
            'color_secundario': cfg.color_secundario,
            'color_texto_header': cfg.color_texto_header,
            'color_fondo_recibo': cfg.color_fondo_recibo,
            'color_texto_principal': cfg.color_texto_principal,
            'color_texto_secundario': cfg.color_texto_secundario,
            'color_borde': cfg.color_borde,
            'color_fondo_monto': cfg.color_fondo_monto,
            # tipografía
            'fuente_familia': cfg.fuente_familia,
            'tamano_fuente_base': cfg.tamano_fuente_base,
            'tamano_titulo': cfg.tamano_titulo,
            'tamano_empresa': cfg.tamano_empresa,
            'fuente_titulo_negrita': cfg.fuente_titulo_negrita,
            # layout
            'estilo_header': cfg.estilo_header,
            'mostrar_banda_decorativa': cfg.mostrar_banda_decorativa,
            'ancho_banda': cfg.ancho_banda,
            'border_radius': cfg.border_radius,
            'mostrar_numero_grande': cfg.mostrar_numero_grande,
            'layout_logo': cfg.layout_logo,
            # tabla
            'tabla_header_texto': cfg.tabla_header_texto,
            'tabla_monto_texto': cfg.tabla_monto_texto,
            'mostrar_columna_codigo': cfg.mostrar_columna_codigo,
        }
