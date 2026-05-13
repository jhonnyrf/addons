# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class FtthWorkOrderAccessory(models.Model):
    """Accesorios utilizados en una orden de trabajo.
    
    Este modelo registra los accesorios/materiales utilizados en cada
    instalación, incluyendo la cantidad y unidad utilizada.
    No gestiona inventario ni stock.
    """
    _name = 'ftth.work.order.accessory'
    _description = 'Accesorio de Orden de Trabajo'
    _rec_name = 'accesorio_id'

    # ==========================================================================
    # Fields
    # ==========================================================================
    work_order_id = fields.Many2one(
        'wigo.ftth.work.order',
        string='Orden de Trabajo',
        ondelete='cascade',
        index=True,
    )

    client_service_id = fields.Many2one(
        'wigo.ftth.client.service',
        string='Ficha Técnica',
        ondelete='cascade',
        index=True,
    )

    accesorio_id = fields.Many2one(
        'ftth.accesorio',
        string='Accesorio',
        required=True,
        domain="[('active', '=', True)]",
        help='Selecciona un accesorio del catálogo.',
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
            ('unidad', 'Unidades'),
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

    @api.constrains('work_order_id', 'client_service_id')
    def _check_relationship(self):
        """Valida que tenga al menos un vínculo: work_order_id o client_service_id."""
        for record in self:
            if not record.work_order_id and not record.client_service_id:
                raise ValidationError('El accesorio debe estar vinculado a una Orden de Trabajo o a una Ficha Técnica.')

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
