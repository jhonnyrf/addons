# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import num2words


class WigoReciboCobro(models.Model):
    """
    Recibo oficial de pago generado desde un registro wigo.pago.estado.
    Se puede imprimir en PDF con logo de empresa.
    Genera dos copias: ORIGINAL (empresa) y COPIA CLIENTE.
    """
    _name = 'wigo.recibo.cobro'
    _description = 'Recibo de Cobro'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'numero desc'
    _rec_name = 'numero'

    numero = fields.Char(
        string='Nº Recibo', required=True, copy=False,
        readonly=True, default='Nuevo', index=True,
    )
    pago_id = fields.Many2one(
        'wigo.pago.estado', string='Pago origen',
        required=True, ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente',
        related='pago_id.partner_id', store=True, readonly=True,
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
        related='pago_id.contract_id', store=True, readonly=True,
    )
    codigo_cliente = fields.Char(
        related='pago_id.codigo_cliente', store=True, readonly=True,
    )
    periodo = fields.Char(
        related='pago_id.periodo', store=True, readonly=True,
    )
    monto = fields.Float(
        string='Monto cobrado (Bs)',
        related='pago_id.monto_pagado', store=True, readonly=True,
    )
    canal_pago = fields.Selection(
        related='pago_id.canal_pago', store=True, readonly=True,
    )
    fecha_pago = fields.Date(
        related='pago_id.fecha_pago', store=True, readonly=True,
    )
    registrado_por = fields.Many2one(
        related='pago_id.registrado_por', store=True, readonly=True,
    )
    monto_en_letras = fields.Char(
        string='Monto en letras', compute='_compute_monto_en_letras', store=True,
    )
    descripcion = fields.Char(
        string='Descripción del servicio',
        compute='_compute_descripcion', store=True, readonly=False,
    )
    # Campos editables para personalizar el recibo
    firma_nombre_override = fields.Char(
        string='Nombre del firmante (override)',
        help='Dejar vacío para usar el del config. Editable antes de emitir.'
    )
    firma_cargo_override = fields.Char(
        string='Cargo (override)',
        help='Dejar vacío para usar el del config. Editable antes de emitir.'
    )
    firma_celular_override = fields.Char(
        string='CEL firmante (override)',
        help='Dejar vacío para usar el del config. Editable antes de emitir.'
    )
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitido', 'Emitido'),
        ('anulado', 'Anulado'),
    ], string='Estado', default='borrador', tracking=True)

    @api.depends('monto')
    def _compute_monto_en_letras(self):
        for rec in self:
            try:
                entero = int(rec.monto)
                decimal = round((rec.monto - entero) * 100)
                texto = num2words.num2words(entero, lang='es').capitalize()
                rec.monto_en_letras = f"{texto} {decimal:02d}/100 Bolivianos"
            except Exception:
                rec.monto_en_letras = ''

    @api.depends('periodo', 'codigo_cliente')
    def _compute_descripcion(self):
        for rec in self:
            if rec.periodo:
                rec.descripcion = f"Servicio Internet {rec.periodo}"
            else:
                rec.descripcion = "Servicio Internet"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('numero', 'Nuevo') == 'Nuevo':
                vals['numero'] = self.env['ir.sequence'].next_by_code('wigo.recibo.cobro') or 'Nuevo'
        return super().create(vals_list)

    def action_emitir(self):
        """Emite el recibo (cambia a estado 'emitido') y vuelve al pago con referencia actualizada."""
        for rec in self:
            if rec.state != 'borrador':
                raise UserError('Solo se pueden emitir recibos en borrador.')
            rec.state = 'emitido'
            rec.message_post(
                body="Recibo emitido exitosamente.",
                message_type='notification',
            )
        # Invalida el cache del pago para que recalcule recibo_id y recibo_generado
        self.ensure_one()
        self.pago_id.invalidate_recordset(['recibo_id', 'recibo_generado'])
        
        # Retorna acción que fuerza reload del form del pago
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wigo.pago.estado',
            'res_id': self.pago_id.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'form': {'reload_on_button': True}},
        }

    def action_volver_borrador(self):
        """Permite regresar a borrador para editar, solo si no está anulado."""
        for rec in self:
            if rec.state == 'anulado':
                raise UserError('No se puede editar un recibo anulado.')
            rec.state = 'borrador'
            rec.message_post(
                body="Recibo regresado a borrador para edición.",
                message_type='notification',
            )

    def action_anular(self):
        """Anula el recibo y vuelve al pago."""
        for rec in self:
            rec.state = 'anulado'
            rec.message_post(
                body="Recibo anulado.",
                message_type='notification',
            )
        # Invalida el cache del pago para que recalcule recibo_id y recibo_generado
        self.ensure_one()
        self.pago_id.invalidate_recordset(['recibo_id', 'recibo_generado'])
        
        # Retorna acción que fuerza reload del form del pago
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wigo.pago.estado',
            'res_id': self.pago_id.id,
            'view_mode': 'form',
            'target': 'current',
            'flags': {'form': {'reload_on_button': True}},
        }

    def action_imprimir(self):
        """Imprime ambas copias (original + copia cliente) en un solo PDF."""
        self.ensure_one()
        if self.state == 'borrador':
            self.state = 'emitido'
        return self.env.ref('wigo_cobranza.action_report_recibo_cobro').report_action(self)

    def action_imprimir_solo_original(self):
        """Imprime solo la copia ORIGINAL (para empresa)."""
        self.ensure_one()
        if self.state == 'borrador':
            self.state = 'emitido'
        return self.env.ref('wigo_cobranza.action_report_recibo_cobro').report_action(self)

    def action_imprimir_copia_cliente(self):
        """Imprime solo la COPIA CLIENTE."""
        self.ensure_one()
        if self.state == 'borrador':
            self.state = 'emitido'
        return self.env.ref('wigo_cobranza.action_report_recibo_cobro').report_action(self)

    def action_preview(self):
        """Abre previsualización del PDF en nueva pestaña"""
        self.ensure_one()
        return self.env.ref('wigo_cobranza.action_report_recibo_cobro').report_action(self)
