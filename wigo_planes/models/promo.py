# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WigoPromo(models.Model):
    """
    Modelo central de Promociones de Wigo.

    Una promoción define las REGLAS de un beneficio comercial.
    Tipos disponibles:
      - referral   → Programa de referidos (N referidos = recompensa)
      - discount   → Descuento porcentual en el plan
      - free_month → Mes gratis (campaña de lanzamiento, zona nueva, etc.)
      - custom     → Cualquier beneficio personalizado libre
    """
    _name = 'wigo.promo'
    _description = 'Promoción Wigo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, name'

    # ── Identificación ────────────────────────────────────────────
    name = fields.Char(
        string='Nombre de la promoción',
        required=True,
        tracking=True,
    )
    promo_type = fields.Selection([
        ('referral',   'Programa de Referidos'),
        ('discount',   'Descuento'),
        ('free_month', 'Mes Gratis'),
        ('custom',     'Personalizado'),
    ], string='Tipo', required=True, default='referral', tracking=True,
       help='Define la mecánica de la promoción.')

    active = fields.Boolean(default=True, tracking=True)
    description = fields.Text(string='Descripción / Condiciones')

    # ── Vigencia ──────────────────────────────────────────────────
    date_start = fields.Date(string='Fecha inicio', required=True,
                             default=fields.Date.today)
    date_end = fields.Date(string='Fecha fin',
                           help='Dejar vacío si la promoción no tiene fecha de vencimiento.')

    # ── Plan asociado (opcional) ──────────────────────────────────
    plan_id = fields.Many2one(
        'internet.plan', string='Plan aplicable',
        domain="[('active','=',True)]",
        help='Si se completa, la promoción aplica solo a este plan. '
             'Dejar vacío = aplica a todos los planes.',
    )

    # ── Configuración según tipo ──────────────────────────────────
    # Referidos
    required_referrals = fields.Integer(
        string='Referidos requeridos',
        default=5,
        help='Solo para tipo "Referidos": cantidad mínima de referidos válidos '
             'para obtener la recompensa.',
    )
    referral_reward_type = fields.Selection([
        ('free_month', 'Mes gratis'),
        ('discount',   'Descuento'),
    ], string='Recompensa del referido', default='free_month',
       help='Solo para tipo "Referidos".')

    # Descuento
    discount_value = fields.Float(
        string='Descuento (%)',
        digits=(5, 2),
        help='Solo para tipo "Descuento" o recompensa de referido con descuento.',
    )

    # Mes gratis / Personalizado
    free_months = fields.Integer(
        string='Meses gratis',
        default=1,
        help='Solo para tipo "Mes Gratis": cuántos meses se aplican.',
    )
    custom_benefit = fields.Char(
        string='Beneficio personalizado',
        help='Solo para tipo "Personalizado": descripción libre del beneficio.',
    )

    # ── Stats ─────────────────────────────────────────────────────
    reward_count = fields.Integer(
        string='Recompensas entregadas',
        compute='_compute_reward_count',
    )
    referral_count = fields.Integer(
        string='Referidos',
        compute='_compute_referral_count',
    )

    # ── Constrains ────────────────────────────────────────────────

    @api.constrains('required_referrals')
    def _check_required_referrals(self):
        for r in self:
            if r.promo_type == 'referral' and r.required_referrals < 1:
                raise ValidationError('Los referidos requeridos deben ser al menos 1.')

    @api.constrains('discount_value', 'promo_type', 'referral_reward_type')
    def _check_discount(self):
        for r in self:
            needs_discount = (
                r.promo_type == 'discount' or
                (r.promo_type == 'referral' and r.referral_reward_type == 'discount')
            )
            if needs_discount and not (0 < r.discount_value <= 100):
                raise ValidationError('El descuento debe estar entre 0.01% y 100%.')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for r in self:
            if r.date_end and r.date_end < r.date_start:
                raise ValidationError('La fecha de fin no puede ser anterior a la de inicio.')

    # ── Computed ──────────────────────────────────────────────────

    def _compute_reward_count(self):
        data = self.env['wigo.promo.reward']._read_group(
            [('promo_id', 'in', self.ids)],
            groupby=['promo_id'],
            aggregates=['__count'],
        )
        mapped = {promo.id: count for promo, count in data if promo}
        for r in self:
            r.reward_count = mapped.get(r.id, 0)

    def _compute_referral_count(self):
        data = self.env['wigo.promo.referral']._read_group(
            [('promo_id', 'in', self.ids)],
            groupby=['promo_id'],
            aggregates=['__count'],
        )
        mapped = {promo.id: count for promo, count in data if promo}
        for r in self:
            r.referral_count = mapped.get(r.id, 0)

    # ── Actions ───────────────────────────────────────────────────

    def action_view_rewards(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Recompensas – {self.name}',
            'res_model': 'wigo.promo.reward',
            'view_mode': 'list,form',
            'domain': [('promo_id', '=', self.id)],
            'context': {'default_promo_id': self.id},
        }

    def action_view_referrals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Referidos – {self.name}',
            'res_model': 'wigo.promo.referral',
            'view_mode': 'list,form',
            'domain': [('promo_id', '=', self.id)],
            'context': {'default_promo_id': self.id},
        }

    @api.model
    def get_active_referral_promo(self):
        """Retorna la promoción de referidos activa más reciente."""
        today = fields.Date.today()
        domain = [
            ('active', '=', True),
            ('promo_type', '=', 'referral'),
            ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
        ]
        return self.search(domain, limit=1, order='date_start desc')
