# -*- coding: utf-8 -*-
from odoo import models, fields


class CancellationReason(models.Model):
    """
    Catálogo editable de motivos de baja.
    El usuario puede agregar, editar o eliminar motivos desde
    CRM > Configuración Bajas > Motivos de Baja.
    """
    _name = 'crm.cancellation.reason'
    _description = 'Motivo de Baja de Servicio'
    _order = 'sequence, name'

    name = fields.Char(string='Motivo', required=True, translate=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
    description = fields.Text(string='Descripción interna')

    # Odoo 19: usar models.Constraint en lugar de _sql_constraints
    _constraints = [
        models.Constraint(
            'unique(name)',
            'Ya existe un motivo con ese nombre.',
        ),
    ]
