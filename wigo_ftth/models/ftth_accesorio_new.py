# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class FtthAccesorio(models.Model):
    """Catálogo de accesorios utilizados en instalaciones FTTH.
    
    Este modelo representa únicamente un catálogo de materiales.
    Los accesorios se asocian a órdenes de trabajo y fichas técnicas
    indicando la cantidad utilizada en cada instalación.
    No gestiona inventario, stock ni movimientos.
    """
    _name = 'ftth.accesorio'
    _description = 'Accesorio FTTH'
    _rec_name = 'name'
    _order = 'name'

    # ==========================================================================
    # Fields
    # ==========================================================================
    name = fields.Char(
        string='Nombre',
        required=True,
        index=True,
    )

    codigo = fields.Char(
        string='Código SKU',
        copy=False,
        help='Código único del accesorio.',
    )

    tipo_unidad = fields.Selection(
        [
            ('m', 'Metros'),
            ('unidad', 'Unidades'),
        ],
        string='Tipo de unidad',
        required=True,
        default='unidad',
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    notas = fields.Html(
        string='Notas',
        help='Información adicional sobre el accesorio.',
    )

    # ==========================================================================
    # Constraints
    # ==========================================================================
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'El nombre del accesorio debe ser único.'),
    ]

    # ==========================================================================
    # Display
    # ==========================================================================
    def name_get(self):
        """Muestra nombre + código en las vistas."""
        result = []
        for record in self:
            name = record.name
            if record.codigo:
                name = f"[{record.codigo}] {record.name}"
            result.append((record.id, name))
        return result
