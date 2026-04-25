# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import num2words


class WigoReciboCobro(models.Model):
    """
    Recibo oficial de pago generado desde un registro wigo.pago.estado.
    Se puede imprimir en PDF con logo de empresa.
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
        required=True, ondelete='restrict',
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
        compute='_compute_descripcion', store=True,
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
        for rec in self:
            if rec.state != 'borrador':
                raise UserError('Solo se pueden emitir recibos en borrador.')
            rec.state = 'emitido'

    def action_anular(self):
        for rec in self:
            rec.state = 'anulado'

    def action_imprimir(self):
        self.ensure_one()
        if self.state == 'borrador':
            self.action_emitir()
        return self.env.ref('wigo_cobranza.action_report_recibo_cobro').report_action(self)
