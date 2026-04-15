# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WigoPromoReferral(models.Model):
    """
    Registro individual de un referido dentro de una promoción.
    Un cliente (referrer) trae a otro cliente (referred) y se registra aquí.
    """
    _name = 'wigo.promo.referral'
    _description = 'Referido de Promoción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    promo_id = fields.Many2one(
        'wigo.promo', string='Promoción',
        required=True, ondelete='restrict',
        domain="[('promo_type','=','referral'),('active','=',True)]",
        default=lambda self: self.env['wigo.promo'].get_active_referral_promo(),
    )
    referrer_id = fields.Many2one(
        'res.partner', string='Cliente referente',
        required=True, index=True, ondelete='restrict',
    )
    referred_id = fields.Many2one(
        'res.partner', string='Cliente referido',
        required=True, index=True, ondelete='restrict',
    )
    state = fields.Selection([
        ('pending',          'Pendiente'),
        ('valid',            'Válido'),
        ('ready_for_reward', 'Listo para recompensa'),
        ('rewarded',         'Recompensado'),
        ('cancelled',        'Cancelado'),
    ], default='pending', required=True, tracking=True, index=True)

    date            = fields.Date(string='Fecha', required=True, default=fields.Date.today, index=True)
    validation_date = fields.Date(string='Fecha de validación', readonly=True)
    ready_date      = fields.Date(string='Listo desde', readonly=True)
    reward_date     = fields.Date(string='Fecha recompensa', readonly=True)
    notes           = fields.Text(string='Notas')

    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── Computed ──────────────────────────────────────────────────

    @api.depends('referrer_id', 'referred_id')
    def _compute_display_name(self):
        for r in self:
            a = r.referrer_id.name or ''
            b = r.referred_id.name or ''
            r.display_name = f'{a} → {b}' if a and b else ''

    # ── Constrains ────────────────────────────────────────────────

    @api.constrains('referrer_id', 'referred_id')
    def _check_no_self_referral(self):
        for r in self:
            if r.referrer_id == r.referred_id:
                raise ValidationError('Un cliente no puede referirse a sí mismo.')

    @api.constrains('referred_id')
    def _check_no_duplicate(self):
        for r in self:
            dup = self.search([
                ('referred_id', '=', r.referred_id.id),
                ('id', '!=', r.id),
                ('state', 'not in', ['cancelled']),
            ], limit=1)
            if dup:
                raise ValidationError(
                    f'"{r.referred_id.name}" ya fue referido por "{dup.referrer_id.name}".'
                )

    # ── Transiciones ──────────────────────────────────────────────

    def action_validate(self):
        for r in self:
            if r.state != 'pending':
                raise ValidationError(f'"{r.display_name}" no está pendiente.')
            r.write({'state': 'valid', 'validation_date': fields.Date.today()})
            r._check_threshold()

    def action_apply_reward(self):
        for r in self:
            if r.state != 'ready_for_reward':
                raise ValidationError(f'"{r.display_name}" no está listo para recompensa.')
        groups = {}
        for r in self:
            key = (r.referrer_id.id, r.promo_id.id)
            groups.setdefault(key, self.env['wigo.promo.referral'])
            groups[key] |= r
        for (partner_id, promo_id), group in groups.items():
            partner = self.env['res.partner'].browse(partner_id)
            promo   = self.env['wigo.promo'].browse(promo_id)
            self._deliver_reward(partner, promo, group)

    def action_apply_reward_all(self):
        """
        Dar recompensa: automáticamente busca y marca TODOS los referidos
        en estado 'ready_for_reward' del mismo referente y promoción.
        No es necesario seleccionarlos manualmente uno por uno.
        """
        groups = {}
        for r in self:
            if r.state != 'ready_for_reward':
                raise ValidationError(f'"{r.display_name}" no está listo para recompensa.')
            key = (r.referrer_id.id, r.promo_id.id)
            groups.setdefault(key, self.env['wigo.promo.referral'])
        # Por cada (referente, promo), buscar TODOS los ready_for_reward automáticamente
        for (partner_id, promo_id), _ in groups.items():
            all_ready = self.search([
                ('referrer_id', '=', partner_id),
                ('promo_id',    '=', promo_id),
                ('state',       '=', 'ready_for_reward'),
            ])
            partner = self.env['res.partner'].browse(partner_id)
            promo   = self.env['wigo.promo'].browse(promo_id)
            self._deliver_reward(partner, promo, all_ready)


    def action_cancel(self):
        for r in self:
            if r.state == 'rewarded':
                raise ValidationError('No se puede cancelar un referido ya recompensado.')
            r.state = 'cancelled'

    def action_reset_to_pending(self):
        for r in self:
            if r.state != 'cancelled':
                raise ValidationError('Solo se pueden reactivar referidos cancelados.')
            r.state = 'pending'

    # ── Lógica interna ────────────────────────────────────────────

    def _check_threshold(self):
        """Tras validar, verifica si el referente ya alcanzó el umbral."""
        self.ensure_one()
        promo = self.promo_id
        valid = self.search([
            ('referrer_id', '=', self.referrer_id.id),
            ('promo_id',    '=', promo.id),
            ('state',       '=', 'valid'),
        ])
        if len(valid) >= promo.required_referrals:
            valid.write({'state': 'ready_for_reward', 'ready_date': fields.Date.today()})
            self.referrer_id.message_post(
                body=(f'🏆 <b>{self.referrer_id.name}</b> alcanzó '
                      f'<b>{len(valid)}</b> referidos válidos en '
                      f'<b>{promo.name}</b>. Listo para recompensa.'),
                message_type='notification',
            )

    def _deliver_reward(self, partner, promo, referrals):
        """Registra la recompensa y marca los referidos como recompensados."""
        reward_type = promo.referral_reward_type
        self.env['wigo.promo.reward'].create({
            'promo_id':      promo.id,
            'partner_id':    partner.id,
            'reward_type':   reward_type,
            'discount_value': promo.discount_value if reward_type == 'discount' else 0,
            'free_months':   1 if reward_type == 'free_month' else 0,
            'notes': f'Generado automáticamente por {len(referrals)} referidos en {promo.name}.',
        })
        referrals.write({'state': 'rewarded', 'reward_date': fields.Date.today()})
        label = dict(promo._fields['referral_reward_type'].selection)[reward_type]
        partner.message_post(
            body=(f'🎉 Recompensa <b>{label}</b> entregada por el programa '
                  f'<b>{promo.name}</b> ({len(referrals)} referidos).'),
            message_type='notification',
        )
        _logger.info('Recompensa "%s" entregada a %s (promo: %s)', reward_type, partner.name, promo.name)

    # ── Cron ──────────────────────────────────────────────────────

    @api.model
    def cron_check_thresholds(self):
        """Recorre referidos válidos y marca los que alcanzaron el umbral."""
        _logger.info('Wigo Planes: verificando umbrales de referidos...')
        promos = self.env['wigo.promo'].search([
            ('active', '=', True), ('promo_type', '=', 'referral')
        ])
        for promo in promos:
            valid = self.search([('promo_id', '=', promo.id), ('state', '=', 'valid')])
            referrers = valid.mapped('referrer_id')
            for referrer in referrers:
                group = valid.filtered(lambda r: r.referrer_id == referrer)
                if len(group) >= promo.required_referrals:
                    group.write({'state': 'ready_for_reward', 'ready_date': fields.Date.today()})
                    referrer.message_post(
                        body=(f'🏆 {referrer.name} tiene {len(group)} referidos listos '
                              f'para recompensa en {promo.name}.'),
                        message_type='notification',
                    )
        _logger.info('Wigo Planes: verificación completada.')


class WigoPromoReward(models.Model):
    """
    Registro de una recompensa entregada a un cliente.
    Se crea automáticamente cuando se aplica una promoción.
    """
    _name = 'wigo.promo.reward'
    _description = 'Recompensa de Promoción'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    promo_id = fields.Many2one(
        'wigo.promo', string='Promoción',
        required=True, ondelete='restrict',
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente',
        required=True, index=True, ondelete='restrict',
    )
    plan_id = fields.Many2one(
        'internet.plan', string='Plan',
        help='Plan sobre el que aplica la recompensa (opcional).',
    )
    reward_type = fields.Selection([
        ('free_month', 'Mes gratis'),
        ('discount',   'Descuento'),
        ('custom',     'Personalizado'),
    ], string='Tipo de recompensa', required=True)

    discount_value = fields.Float(string='Descuento (%)', digits=(5, 2))
    free_months    = fields.Integer(string='Meses gratis', default=1)
    custom_detail  = fields.Char(string='Detalle del beneficio')

    state = fields.Selection([
        ('pending',   'Pendiente de aplicar'),
        ('applied',   'Aplicada'),
        ('cancelled', 'Cancelada'),
    ], default='pending', required=True, tracking=True)

    date       = fields.Date(string='Fecha', default=fields.Date.today, required=True)
    apply_date = fields.Date(string='Fecha de aplicación', readonly=True)
    notes      = fields.Text(string='Notas')

    def action_mark_applied(self):
        for r in self:
            r.write({'state': 'applied', 'apply_date': fields.Date.today()})

    def action_cancel(self):
        for r in self:
            if r.state == 'applied':
                raise ValidationError('No se puede cancelar una recompensa ya aplicada.')
            r.state = 'cancelled'
