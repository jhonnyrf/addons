# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ReciboViewer(models.TransientModel):
    """
    Wizard modal para ver opciones de impresión y gestión del recibo.
    Se abre cuando el usuario hace click en "Ver Recibo".
    """
    _name = 'recibo.viewer'
    _description = 'Ver Recibo - Opciones de Impresión'

    recibo_id = fields.Many2one(
        'wigo.recibo.cobro',
        string='Recibo',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='recibo_id.partner_id',
        readonly=True,
    )
    numero_recibo = fields.Char(
        related='recibo_id.numero',
        readonly=True,
    )
    monto = fields.Float(
        related='recibo_id.monto',
        readonly=True,
    )
    estado = fields.Selection(
        related='recibo_id.state',
        readonly=True,
    )

    def action_imprimir_ambas(self):
        """Imprime ambas copias."""
        return self.recibo_id.action_imprimir()

    def action_imprimir_original(self):
        """Imprime solo copia original."""
        return self.recibo_id.action_imprimir_solo_original()

    def action_imprimir_copia(self):
        """Imprime solo copia cliente."""
        return self.recibo_id.action_imprimir_copia_cliente()

    def action_editar(self):
        """Vuelve a borrador para editar."""
        self.recibo_id.action_volver_borrador()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wigo.recibo.cobro',
            'res_id': self.recibo_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_anular(self):
        """Anula el recibo y cierra el wizard."""
        return self.recibo_id.action_anular()
