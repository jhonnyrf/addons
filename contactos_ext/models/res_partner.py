# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _WIGO_INSTALLATION_FIELDS = ('zona', 'direccion', 'ubicacion', 'coordenadas')

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if 'company_type' in fields_list and not values.get('company_type'):
            values['company_type'] = 'person'
        if 'is_company' in fields_list and 'is_company' not in values:
            values['is_company'] = False
        return values

    # ── Identificación ────────────────────────────────────────────
    ci = fields.Char(string="CI")
    celular = fields.Char(string="Celular")

    # ── Datos de instalación Wigo ─────────────────────────────────
    zona = fields.Char(string="Zona")
    zona_id = fields.Many2one(
        'wigo.zone',
        string="Zona",
        compute='_compute_zona_id',
        inverse='_inverse_zona_id',
        store=False,
        help="Seleccione una zona existente o cree una nueva.",
    )
    direccion = fields.Char(string="Dirección")
    ubicacion = fields.Char(string="Ubicación")
    coordenadas = fields.Char(string="Coordenadas")

    @api.depends('zona')
    def _compute_zona_id(self):
        Zone = self.env['wigo.zone']
        for partner in self:
            value = (partner.zona or '').strip()
            if not value:
                partner.zona_id = False
                continue
            zone = Zone.search([('name', '=ilike', value)], limit=1)
            if not zone:
                zone = Zone.create({'name': value})
            partner.zona_id = zone

    def _inverse_zona_id(self):
        for partner in self:
            partner.zona = partner.zona_id.name if partner.zona_id else False

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if not self.env.context.get('skip_partner_to_lead_sync'):
            partners._sync_wigo_installation_to_leads()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if (
            not self.env.context.get('skip_partner_to_lead_sync')
            and any(field in vals for field in self._WIGO_INSTALLATION_FIELDS)
        ):
            self._sync_wigo_installation_to_leads()
        return res

    def _sync_wigo_installation_to_leads(self):
        Lead = self.env['crm.lead']
        for partner in self:
            if not partner.id:
                continue
            leads = Lead.search([('partner_id', '=', partner.id)])
            if not leads:
                continue
            vals = {
                'zona': partner.zona or False,
                'direccion': partner.direccion or False,
                'ubicacion': partner.ubicacion or False,
                'coordenadas': partner.coordenadas or False,
            }
            leads.with_context(skip_lead_to_partner_sync=True).write(vals)

    # ── Planes contratados ────────────────────────────────────────
    partner_plan_ids = fields.One2many(
        'partner.plan', 'partner_id',
        string='Planes contratados',
    )
    active_plan_count = fields.Integer(
        string='Planes activos',
        compute='_compute_plan_counts',
        store=True,
    )
    total_plan_count = fields.Integer(
        string='Total de planes',
        compute='_compute_plan_counts',
        store=True,
    )

    @api.depends('partner_plan_ids', 'partner_plan_ids.state')
    def _compute_plan_counts(self):
        for partner in self:
            plans = partner.partner_plan_ids
            partner.total_plan_count = len(plans)
            partner.active_plan_count = len(
                plans.filtered(lambda p: p.state == 'active')
            )

    def action_view_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Planes de {self.name}',
            'res_model': 'partner.plan',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    # ── Referidos (fuente: wigo.promo.referral) ───────────────────
    # Personas que YO recomendé (yo soy el referente)
    referral_as_referrer_ids = fields.One2many(
        'wigo.promo.referral', 'referrer_id',
        string='Referidos que hice',
    )
    # Registro donde YO fui el referido (quién me recomendó a mí)
    referral_as_referred_ids = fields.One2many(
        'wigo.promo.referral', 'referred_id',
        string='Fui referido por',
    )

    # Contador: solo los que YO recomendé (estados activos)
    referral_count = fields.Integer(
        string='Referidos',
        compute='_compute_referral_count',
        store=False,
    )

    @api.depends('referral_as_referrer_ids')
    def _compute_referral_count(self):
        result = self.env['wigo.promo.referral'].read_group(
            domain=[
                ('referrer_id', 'in', self.ids),
                ('state', 'not in', ['cancelled']),
            ],
            fields=['referrer_id'],
            groupby=['referrer_id'],
        )
        counts = {r['referrer_id'][0]: r['referrer_id_count'] for r in result}
        for partner in self:
            partner.referral_count = counts.get(partner.id, 0)

    def action_view_referrals(self):
        """Abre los referidos que este contacto realizó."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Referidos por {self.name}',
            'res_model': 'wigo.promo.referral',
            'view_mode': 'list,form',
            'domain': [('referrer_id', '=', self.id)],
            'context': {'default_referrer_id': self.id},
        }

    # ── Otros campos ──────────────────────────────────────────────
    is_employee = fields.Boolean(string='Es empleado')

    lead_ids = fields.One2many(
        'crm.lead', 'partner_id',
        string='Oportunidades CRM',
    )
