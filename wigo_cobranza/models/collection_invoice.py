from datetime import datetime
from markupsafe import Markup
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


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
    notas = fields.Html(string='Notas')

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
            self._post_factura_created_message(rec)
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

    def write(self, vals):
        """Override write to log field changes to chatter."""
        # Fields to track for logging
        tracked_fields = {
            'numero_factura', 'numero_autorizacion', 'monto_total',
            'descuento', 'razon_social', 'nit_ci', 'fecha_emision', 'notas', 'state'
        }
        
        for rec in self:
            changed_fields = {}
            state_changed = False
            old_state = rec.state
            
            # Detect field changes
            for field_name in tracked_fields:
                if field_name in vals:
                    old_val = rec[field_name]
                    new_val = vals[field_name]
                    
                    if old_val != new_val:
                        if field_name == 'state':
                            state_changed = True
                        else:
                            changed_fields[field_name] = (old_val, new_val)
            
            # Execute the write
            result = super(WigoFacturaCobranza, rec).write(vals)
            
            # Log state change
            if state_changed and old_state != vals.get('state'):
                rec._post_estado_changed_message(rec, old_state)
            
            # Log other field changes
            if changed_fields:
                rec._post_field_changes_message(rec, changed_fields)
            
            return result
        
        return super().write(vals)

    def action_marcar_pagada(self):
        for rec in self:
            rec.state = 'emitido'
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            user_name = self.env.user.name
            body = Markup(
                f'<strong style="color: #28a745;">✓ Factura Emitida Manualmente</strong><br/>'
                f'<small>{timestamp} por <strong>{user_name}</strong></small>'
            )
            rec.message_post(body=body, subtype_xmlid='mail.mt_note')

    def action_emitir(self):
        self.ensure_one()
        self.state = 'emitido'
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name
        body = Markup(
            f'<strong style="color: #28a745;">✓ Factura Emitida</strong><br/>'
            f'<small>{timestamp} por <strong>{user_name}</strong></small>'
        )
        self.message_post(body=body, subtype_xmlid='mail.mt_note')
        return {'type': 'ir.actions.act_window_close'}

    def action_anular(self):
        for rec in self:
            rec.state = 'anulada'
            self._post_factura_cancelled_message(rec)

    # ─────────────────────────────────────────────────────────────
    # Chatter Logging Methods
    # ─────────────────────────────────────────────────────────────

    def _post_factura_created_message(self, rec):
        """Log factura creation to chatter."""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name
        body = Markup(
            f'<strong>✓ Factura Creada</strong><br/>'
            f'<small>{timestamp} por <strong>{user_name}</strong></small><br/>'
            f'<ul style="margin: 8px 0; padding-left: 20px;">'
            f'  <li>Nº Factura: <strong>{rec.numero_factura}</strong></li>'
            f'  <li>Cliente: <strong>{rec.partner_id.name}</strong></li>'
            f'  <li>Período: <strong>{rec.periodo_facturado}</strong></li>'
            f'  <li>Monto: <strong>Bs. {rec.monto_neto:.2f}</strong></li>'
            f'  <li>Estado: <strong style="color: #ffc107;">Pendiente</strong></li>'
            f'</ul>'
        )
        rec.message_post(body=body, subtype_xmlid='mail.mt_note')

    def _post_estado_changed_message(self, rec, old_state):
        """Log state change to chatter."""
        state_display = dict(rec._fields['state'].selection)
        old_display = state_display.get(old_state, old_state)
        new_display = state_display.get(rec.state, rec.state)
        
        state_colors = {
            'pendiente': '#ffc107',
            'emitido': '#28a745',
            'anulada': '#dc3545',
        }
        old_color = state_colors.get(old_state, '#999')
        new_color = state_colors.get(rec.state, '#999')
        
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name
        body = Markup(
            f'<strong>→ Cambio de Estado</strong><br/>'
            f'<small>{timestamp} por <strong>{user_name}</strong></small><br/>'
            f'<div style="margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">'
            f'  <span style="color: {old_color}; font-weight: bold;">●</span> {old_display} '
            f'  <span style="margin: 0 6px;">→</span> '
            f'  <span style="color: {new_color}; font-weight: bold;">●</span> {new_display}'
            f'</div>'
        )
        rec.message_post(body=body, subtype_xmlid='mail.mt_note')

    def _post_factura_cancelled_message(self, rec):
        """Log factura cancellation to chatter."""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name
        body = Markup(
            f'<strong style="color: #dc3545;">✕ Factura Anulada</strong><br/>'
            f'<small>{timestamp} por <strong>{user_name}</strong></small><br/>'
            f'<p style="margin: 8px 0; color: #666;">Esta factura ha sido anulada y no puede ser modificada.</p>'
        )
        rec.message_post(body=body, subtype_xmlid='mail.mt_note')

    def _post_field_changes_message(self, rec, changed_fields):
        """Log field changes to chatter."""
        if not changed_fields:
            return
        
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name
        
        field_labels = {
            'numero_factura': 'Nº Factura',
            'numero_autorizacion': 'Nº Autorización SIAT',
            'monto_total': 'Monto Total',
            'descuento': 'Descuento',
            'razon_social': 'Razón Social',
            'nit_ci': 'NIT / CI',
            'fecha_emision': 'Fecha de Emisión',
            'notas': 'Notas',
        }
        
        changes_html = ''
        for field_name, (old_val, new_val) in changed_fields.items():
            label = field_labels.get(field_name, field_name)
            old_str = f'<strong>{old_val}</strong>' if old_val else '<em>—</em>'
            new_str = f'<strong>{new_val}</strong>' if new_val else '<em>—</em>'
            changes_html += (
                f'<li><strong>{label}:</strong> {old_str} → {new_str}</li>'
            )
        
        body = Markup(
            f'<strong>✎ Cambios Registrados</strong><br/>'
            f'<small>{timestamp} por <strong>{user_name}</strong></small><br/>'
            f'<ul style="margin: 8px 0; padding-left: 20px;">'
            f'{changes_html}'
            f'</ul>'
        )
        rec.message_post(body=body, subtype_xmlid='mail.mt_note')
