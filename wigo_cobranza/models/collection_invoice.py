from odoo import models, fields, api


class WigoFacturaCobranza(models.Model):
    _name = 'wigo.factura.cobranza'
    _description = 'Collection Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_emision desc'
    _rec_name = 'numero_factura'

    numero_factura = fields.Char(
        string='Nº Factura', required=True, tracking=True, index=True,
    )
    numero_autorizacion = fields.Char(
        string='Nº Autorización SIAT', tracking=True,
    )
    pago_id = fields.Many2one(
        'wigo.pago.estado', string='Pago asociado',
        ondelete='restrict', tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente',
        required=True, ondelete='restrict', tracking=True,
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato', tracking=True,
    )
    codigo_cliente = fields.Char(
        string='Código CF', compute='_compute_codigo', store=True,
    )
    razon_social = fields.Char(
        string='Razón social / Nombre', required=True,
        compute='_compute_datos_factura', store=True, readonly=False,
    )
    nit_ci = fields.Char(
        string='NIT / CI',
        compute='_compute_datos_factura', store=True, readonly=False,
    )
    fecha_emision = fields.Date(
        string='Fecha de emisión', required=True,
        default=lambda self: fields.Date.context_today(self), tracking=True,
    )
    periodo_facturado = fields.Char(
        string='Período facturado', tracking=True,
    )
    monto_total = fields.Float(
        string='Monto total (Bs)', required=True, tracking=True,
    )
    descuento = fields.Float(
        string='Descuento (Bs)', tracking=True,
    )
    monto_neto = fields.Float(
        string='Monto neto (Bs)',
        compute='_compute_monto_neto', store=True,
    )
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('emitido', 'Emitido'),
        ('anulada', 'Anulada'),
    ], string='Estado', default='pendiente', required=True, tracking=True, index=True)
    notas = fields.Text(string='Notas')

    @api.depends('contract_id', 'pago_id')
    def _compute_codigo(self):
        for rec in self:
            rec.codigo_cliente = (
                rec.pago_id.codigo_cliente or rec.contract_id.name or False
            )

    @api.depends('partner_id')
    def _compute_datos_factura(self):
        for rec in self:
            if rec.partner_id:
                rec.razon_social = rec.partner_id.name or ''
                rec.nit_ci = (
                    getattr(rec.partner_id, 'ci', False) or
                    getattr(rec.partner_id, 'vat', False) or ''
                )
            else:
                rec.razon_social = ''
                rec.nit_ci = ''

    @api.depends('monto_total', 'descuento')
    def _compute_monto_neto(self):
        for rec in self:
            rec.monto_neto = rec.monto_total - rec.descuento

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records.filtered(lambda r: r.state != 'anulada'):
            rec.write({'state': 'emitido'})
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification',
                {
                    'title': 'Factura Emitida',
                    'message': f'Factura {rec.numero_factura} emitida correctamente',
                    'sticky': False,
                }
            )
        for rec in records.filtered(lambda r: r.state == 'anulada'):
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification',
                {
                    'title': 'Factura Anulada',
                    'message': f'Factura {rec.numero_factura} ha sido anulada',
                    'sticky': False,
                }
            )
        return records

    @api.onchange('pago_id')
    def _onchange_pago_id(self):
        if self.pago_id:
            self.partner_id = self.pago_id.partner_id
            self.contract_id = self.pago_id.contract_id
            self.monto_total = self.pago_id.monto_pagado
            self.periodo_facturado = self.pago_id.periodo
            if self.pago_id.fecha_pago:
                self.fecha_emision = self.pago_id.fecha_pago

    def action_marcar_pagada(self):
        for rec in self:
            rec.state = 'emitido'

    def action_emitir(self):
        self.ensure_one()
        self.state = 'emitido'
        return {'type': 'ir.actions.act_window_close'}

    def action_anular(self):
        for rec in self:
            rec.state = 'anulada'
