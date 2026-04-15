# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ── Identificación ────────────────────────────────────────────
    ci = fields.Char(string="CI")
    celular = fields.Char(string="Celular")

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
