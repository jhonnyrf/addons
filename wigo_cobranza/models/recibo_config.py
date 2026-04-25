# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WigoReciboConfig(models.Model):
    """
    Configuración visual del recibo de cobranza.
    Singleton (un solo registro). Permite editar logo,
    datos de empresa y firma desde la interfaz sin tocar código.
    """
    _name = 'wigo.recibo.config'
    _description = 'Configuración del Recibo de Cobro'

    name = fields.Char(default='Configuración del Recibo', readonly=True)

    # ── Empresa ──────────────────────────────────────────────────
    empresa_nombre = fields.Char(
        string='Nombre empresa', default='WIGO FAST',
    )
    empresa_direccion = fields.Char(
        string='Dirección', default='Calle Junin Nº 425',
    )
    empresa_ciudad = fields.Char(
        string='Ciudad', default='Cochabamba',
    )
    empresa_celular = fields.Char(
        string='CEL empresa', default='63888133',
    )

    # ── Logo ─────────────────────────────────────────────────────
    logo = fields.Binary(
        string='Logo del recibo',
        help='Suba el logo que aparecerá en el recibo PDF. Recomendado: fondo transparente, aprox. 300×120 px.',
    )
    logo_fname = fields.Char(string='Nombre del archivo logo')
    usar_logo_imagen = fields.Boolean(
        string='Usar logo imagen (si no, mostrar texto)',
        default=False,
    )

    # ── Firma ────────────────────────────────────────────────────
    firma_nombre = fields.Char(
        string='Nombre firmante', default='Lic. Patricia Villarroel',
    )
    firma_cargo = fields.Char(
        string='Cargo', default='CONTABILIDAD',
    )
    firma_celular = fields.Char(
        string='CEL firmante', default='68582771',
    )

    @api.model
    def get_config(self):
        """Retorna el singleton de configuración, creándolo si no existe."""
        config = self.search([], limit=1)
        if not config:
            config = self.create({})
        return config
