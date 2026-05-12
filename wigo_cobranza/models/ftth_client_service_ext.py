from odoo import models, fields, api


class FtthClientServiceCobranza(models.Model):
    _inherit = 'wigo.ftth.client.service'

    estado_pago = fields.Selection([
        ('al_dia', 'Al día'),
        ('pendiente', 'Pendiente'),
        ('mora', 'En mora'),
        ('deuda_parcial', 'Deuda parcial'),
        ('baja_definitiva', 'Baja definitiva'),
    ], string='Estado de pago', default='pendiente',
       tracking=True, index=True,
    )

    pago_ids = fields.One2many(
        'wigo.pago.estado', 'client_service_id',
        string='Historial de pagos',
    )
    total_pagos = fields.Integer(
        string='Total pagos registrados',
        compute='_compute_total_pagos',
    )
    ultimo_pago_fecha = fields.Date(
        string='Último pago', compute='_compute_last_payment_date', store=True,
    )

    monto_prorrateo_primer_mes = fields.Float(
        string='Prorrateo primer mes (Bs)',
        compute='_compute_proration_info',
    )

    @api.depends('pago_ids')
    def _compute_total_pagos(self):
        for rec in self:
            rec.total_pagos = len(rec.pago_ids)

    @api.depends('pago_ids.fecha_pago', 'pago_ids.estado_pago')
    def _compute_last_payment_date(self):
        for rec in self:
            pagados = rec.pago_ids.filtered(
                lambda p: p.estado_pago == 'al_dia' and p.fecha_pago
            )
            rec.ultimo_pago_fecha = max(pagados.mapped('fecha_pago')) if pagados else False

    @api.depends('fecha_instalacion', 'plan_id')
    def _compute_proration_info(self):
        import calendar
        from datetime import date
        for rec in self:
            if not rec.fecha_instalacion or not rec.plan_id:
                rec.monto_prorrateo_primer_mes = 0.0
                continue
            fi = rec.fecha_instalacion
            dias_mes = calendar.monthrange(fi.year, fi.month)[1]
            dias_restantes = dias_mes - fi.day + 1
            rec.monto_prorrateo_primer_mes = round(
                (rec.plan_id.price / dias_mes) * dias_restantes, 2
            )

    def action_ver_pagos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Pagos -- {self.codigo_cliente}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'domain': [('client_service_id', '=', self.id)],
            'context': {
                'default_client_service_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

    def action_crear_pago_mes(self):
        from datetime import date
        hoy = date.today()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar Pago',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_client_service_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_mes': str(hoy.month),
                'default_anio': hoy.year,
            },
        }
