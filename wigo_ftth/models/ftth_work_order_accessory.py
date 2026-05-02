# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class FtthWorkOrderAccessory(models.Model):
    """Accesorios utilizados en una orden de trabajo."""
    _name = 'ftth.work.order.accessory'
    _description = 'Accesorio de Orden de Trabajo'
    _rec_name = 'accesorio_id'

    # ==========================================================================
    # Fields
    # ==========================================================================
    work_order_id = fields.Many2one(
        'wigo.ftth.work.order',
        string='Orden de Trabajo',
        required=True,
        ondelete='cascade',
        index=True,
    )

    accesorio_id = fields.Many2one(
        'ftth.accesorio',
        string='Accesorio',
        required=True,
        domain="[('active', '=', True), ('cantidad_disponible', '>', 0)]",
        help='Solo se pueden seleccionar accesorios con stock disponible.',
    )

    cantidad = fields.Float(
        string='Cantidad utilizada',
        required=True,
        default=1.0,
        help='Cantidad del accesorio utilizado en esta instalación.',
    )

    unidad = fields.Selection(
        [
            ('m', 'Metros'),
            ('unidad', 'Unidad'),
        ],
        string='Unidad',
        related='accesorio_id.tipo_unidad',
        store=True,
        readonly=True,
    )

    # ==========================================================================
    # Constraints
    # ==========================================================================
    @api.constrains('cantidad')
    def _check_cantidad_positiva(self):
        """Valida que la cantidad sea positiva."""
        for record in self:
            if record.cantidad <= 0:
                raise ValidationError('La cantidad debe ser mayor a 0.')

    @api.constrains('cantidad', 'accesorio_id')
    def _check_cantidad_vs_stock(self):
        """Valida que la cantidad no supere el stock disponible."""
        for record in self:
            if record.accesorio_id and record.accesorio_id.cantidad_disponible < record.cantidad:
                raise ValidationError(
                    f"Stock insuficiente de '{record.accesorio_id.name}'. "
                    f"Disponible: {record.accesorio_id.cantidad_disponible}, "
                    f"Requerido: {record.cantidad}"
                )

    # ==========================================================================
    # Display
    # ==========================================================================
    def name_get(self):
        """Muestra descripción legible del accesorio."""
        result = []
        for record in self:
            name = f"{record.accesorio_id.name} ({record.cantidad} {record.unidad})"
            result.append((record.id, name))
        return result
