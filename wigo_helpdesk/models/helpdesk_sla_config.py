# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HelpdeskSlaConfig(models.Model):
    """
    Configuración global del semáforo SLA.
    Registro singleton (solo uno por compañía).
    Define los umbrales de tiempo que disparan cada color del semáforo.
    """
    _name = 'helpdesk.sla.config'
    _description = 'Configuración de Semáforo SLA'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre',
        default='Configuración SLA',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True,
    )

    # ── ZONA VERDE ─────────────────────────────────────────────────────────────
    ok_label = fields.Char(
        string='Etiqueta Verde',
        default='En tiempo',
        required=True,
        help='Texto que aparece en el badge verde del semáforo.',
    )
    ok_icon = fields.Char(
        string='Ícono Verde (FA)',
        default='fa-check-circle',
        help='Clase FontAwesome, ej: fa-check-circle',
    )
    ok_color = fields.Char(
        string='Color Verde (CSS)',
        default='#28a745',
        help='Color hexadecimal o nombre CSS para el badge verde.',
    )

    # ── ZONA AMARILLA ──────────────────────────────────────────────────────────
    warning_label = fields.Char(
        string='Etiqueta Amarilla',
        default='Próximo a vencer',
        required=True,
    )
    warning_icon = fields.Char(
        string='Ícono Amarillo (FA)',
        default='fa-clock-o',
    )
    warning_color = fields.Char(
        string='Color Amarillo (CSS)',
        default='#ffc107',
    )
    # Porcentaje de tiempo restante a partir del cual pasa a amarillo
    warning_threshold_pct = fields.Float(
        string='Umbral Amarillo (%)',
        default=25.0,
        help=(
            'Cuando el tiempo restante sea menor a este % del total SLA, '
            'el semáforo cambia a amarillo. Ej: 25 = menos del 25% restante.'
        ),
    )
    # Horas absolutas de aviso (alternativa/complemento al %)
    warning_threshold_hours = fields.Float(
        string='Umbral Amarillo (horas absolutas)',
        default=0.0,
        help=(
            'Si > 0, el semáforo pasa a amarillo cuando queden MENOS de estas horas, '
            'independientemente del %. Se usa el criterio que antes se active.'
        ),
    )

    # ── ZONA ROJA ──────────────────────────────────────────────────────────────
    danger_label = fields.Char(
        string='Etiqueta Roja',
        default='SLA Vencido',
        required=True,
    )
    danger_icon = fields.Char(
        string='Ícono Rojo (FA)',
        default='fa-exclamation-circle',
    )
    danger_color = fields.Char(
        string='Color Rojo (CSS)',
        default='#dc3545',
    )

    # ── ZONA GRIS (cerrado) ────────────────────────────────────────────────────
    closed_label = fields.Char(
        string='Etiqueta Cerrado',
        default='Cerrado',
        required=True,
    )
    closed_icon = fields.Char(
        string='Ícono Cerrado (FA)',
        default='fa-check',
    )
    closed_color = fields.Char(
        string='Color Cerrado (CSS)',
        default='#6c757d',
    )

    # ── SLA POR PRIORIDAD ──────────────────────────────────────────────────────
    sla_hours_critical = fields.Float(
        string='SLA Prioridad Crítica (horas)',
        default=4.0,
        required=True,
        help='Horas máximas para tickets de prioridad Crítica.',
    )
    sla_hours_high = fields.Float(
        string='SLA Prioridad Alta (horas)',
        default=24.0,
        required=True,
    )
    sla_hours_medium = fields.Float(
        string='SLA Prioridad Media (horas)',
        default=48.0,
        required=True,
    )
    sla_hours_low = fields.Float(
        string='SLA Prioridad Baja (horas)',
        default=72.0,
        required=True,
    )

    # ── CRON SETTINGS ─────────────────────────────────────────────────────────
    escalate_on_expire = fields.Boolean(
        string='Escalar automáticamente al vencer SLA',
        default=True,
        help='Si está activo, el cron moverá los tickets vencidos a la etapa "En Espera".',
    )
    notify_on_warning = fields.Boolean(
        string='Notificar al responsable cuando entre en zona amarilla',
        default=True,
    )

    default_ticket_sla_days = fields.Integer(
        string='Dias SLA por defecto en tickets',
        compute='_compute_default_ticket_sla_days',
        inverse='_inverse_default_ticket_sla_days',
        store=False,
        help='Valor por defecto para selector rapido de SLA (1 a 7 dias).',
    )

    # ── SINGLETON ─────────────────────────────────────────────────────────────
    @api.model
    def get_config(self):
        """Devuelve la configuración activa (crea una por defecto si no existe)."""
        config = self.search([('company_id', '=', self.env.company.id)], limit=1)
        if not config:
            config = self.create({'name': 'Configuración SLA', 'company_id': self.env.company.id})
        return config

    def action_open_config(self):
        """Acción que abre siempre el formulario del singleton."""
        config = self.get_config()
        return {
            'type': 'ir.actions.act_window',
            'name': '🚦 Semáforo SLA',
            'res_model': 'helpdesk.sla.config',
            'view_mode': 'form',
            'res_id': config.id,
            'target': 'current',
        }

    @api.model
    def get_sla_hours_by_priority(self, priority):
        """Devuelve las horas SLA configuradas para una prioridad dada."""
        config = self.get_config()
        return {
            '3': config.sla_hours_critical,
            '2': config.sla_hours_high,
            '1': config.sla_hours_medium,
            '0': config.sla_hours_low,
        }.get(str(priority), config.sla_hours_medium)

    def _compute_default_ticket_sla_days(self):
        key_tpl = 'wigo_helpdesk.default_ticket_sla_days.%s'
        for rec in self:
            key = key_tpl % (rec.company_id.id or self.env.company.id)
            raw = self.env['ir.config_parameter'].sudo().get_param(key, default='2')
            try:
                val = int(raw)
            except (TypeError, ValueError):
                val = 2
            rec.default_ticket_sla_days = min(max(val, 1), 7)

    def _inverse_default_ticket_sla_days(self):
        key_tpl = 'wigo_helpdesk.default_ticket_sla_days.%s'
        for rec in self:
            key = key_tpl % (rec.company_id.id or self.env.company.id)
            val = min(max(int(rec.default_ticket_sla_days or 2), 1), 7)
            self.env['ir.config_parameter'].sudo().set_param(key, str(val))

    @api.model
    def get_default_ticket_sla_days(self):
        company_id = self.env.company.id
        key = 'wigo_helpdesk.default_ticket_sla_days.%s' % company_id
        raw = self.env['ir.config_parameter'].sudo().get_param(key, default='2')
        try:
            days = int(raw)
        except (TypeError, ValueError):
            days = 2
        return min(max(days, 1), 7)
