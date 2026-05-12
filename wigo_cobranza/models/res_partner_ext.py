from odoo import models, fields, api


class ResPartnerCobranza(models.Model):
    _inherit = 'res.partner'

    active_contract_count = fields.Integer(
        string='Contratos activos',
        compute='_compute_contract_counters',
    )
    contract_any_count = fields.Integer(
        string='Total contratos',
        compute='_compute_contract_counters',
    )
    cobranza_ci = fields.Char(
        string='CI', compute='_compute_contact_snapshot',
    )
    cobranza_celular = fields.Char(
        string='Celular', compute='_compute_contact_snapshot',
    )
    cobranza_zona = fields.Char(
        string='Zona', compute='_compute_contact_snapshot',
    )
    cobranza_direccion = fields.Char(
        string='Direccion', compute='_compute_contact_snapshot',
    )
    cobranza_contact_url = fields.Char(
        string='Ficha contacto', compute='_compute_contact_snapshot',
    )
    cobranza_pago_ids = fields.One2many(
        'wigo.pago.estado', 'partner_id',
        string='Historial mensual de cobros',
    )
    cobranza_pago_count = fields.Integer(
        string='Meses registrados',
        compute='_compute_cobranza_pago_count',
    )

    @api.depends('cobranza_pago_ids')
    def _compute_cobranza_pago_count(self):
        for partner in self:
            partner.cobranza_pago_count = len(partner.cobranza_pago_ids)

    @api.depends('contract_ids', 'contract_ids.state')
    def _compute_contract_counters(self):
        for partner in self:
            contracts = partner.contract_ids.filtered(lambda c: not c.is_superseded)
            partner.contract_any_count = len(contracts)
            partner.active_contract_count = len(contracts.filtered(lambda c: c.state == 'active'))

    @api.depends('name', 'phone', 'email')
    def _compute_contact_snapshot(self):
        for partner in self:
            partner.cobranza_ci = getattr(partner, 'ci', False) or False
            partner.cobranza_celular = getattr(partner, 'celular', False) or getattr(partner, 'mobile', False) or False
            partner.cobranza_zona = getattr(partner, 'zona', False) or False
            partner.cobranza_direccion = getattr(partner, 'direccion', False) or getattr(partner, 'street', False) or False
            partner.cobranza_contact_url = f"#id={partner.id}&model=res.partner&view_type=form"

    def action_view_cobranza_pagos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Cobranza mensual - {self.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_cobranza_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contratos - {self.name}',
            'res_model': 'customer.contract',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('state', '=', 'active'),
                ('is_superseded', '=', False),
            ],
            'context': {
                'default_partner_id': self.id,
                'search_default_active': 1,
            },
        }

    def action_open_contact_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contacto - {self.name}',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_registrar_factura_desde_cliente(self):
        self.ensure_one()
        contract = self.contract_ids.filtered(
            lambda c: c.state == 'active' and not c.is_superseded
        )[:1]
        ctx = {
            'default_partner_id': self.id,
            'default_razon_social': self.name,
            'default_nit_ci': getattr(self, 'cobranza_ci', '') or getattr(self, 'vat', '') or '',
        }
        if contract:
            ctx['default_contract_id'] = contract.id
        return {
            'type': 'ir.actions.act_window',
            'name': f'Nueva Factura -- {self.name}',
            'res_model': 'wigo.factura.cobranza',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_registrar_incobrable_desde_cliente(self):
        self.ensure_one()
        contract = self.contract_ids.filtered(
            lambda c: not c.is_superseded
        )[:1]
        svc = self.env['wigo.ftth.client.service'].search(
            [('partner_id', '=', self.id)], limit=1
        )
        ctx = {'default_partner_id': self.id}
        if contract:
            ctx['default_contract_id'] = contract.id
        if svc:
            ctx['default_client_service_id'] = svc.id
        return {
            'type': 'ir.actions.act_window',
            'name': f'Declarar Incobrable -- {self.name}',
            'res_model': 'wigo.incobrable',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }
