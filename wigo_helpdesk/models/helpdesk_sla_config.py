# -*- coding: utf-8 -*-
from odoo import models, fields, api


# Prioridades SLA por defecto
PRIORIDADES_DEFAULT = [
    (10, 'Muy Alta',  '#e53935', 24.0,  'Inmediato (30 min. Después de notificación ya se debe estar atendiendo)'),
    (20, 'Alta',      '#f57c00', 72.0,  'Inmediato según orden de prelación'),
    (30, 'Media',     '#fdd835', 72.0,  'Priorizado según orden de prelación'),
    (40, 'Baja',      '#8bc34a', 48.0,  'Priorizado según orden de prelación'),
    (50, 'Crítica',   '#7b0000',  6.0,  'Inmediato (15 min. Después de notificación ya se debe estar atendiendo)'),
]


class HelpdeskSlaConfig(models.Model):
    """
    Configuración global del semáforo SLA (única para todo el sistema).
    """
    _name = 'helpdesk.sla.config'
    _description = 'Configuración de Semáforo SLA'
    _rec_name = 'name'
    _sql_constraints = [
        ('unique_single', 'CHECK(1=1)', 'Solo puede haber una configuración SLA'),
    ]

    name = fields.Char(string='Nombre', default='Configuración SLA', required=True)

    # ── ZONA VERDE ────────────────────────────────────────────────────────────
    ok_label = fields.Char(string='Etiqueta Verde', default='En tiempo', required=True)
    ok_icon = fields.Char(string='Ícono Verde (FA)', default='fa-check-circle')
    ok_color = fields.Char(string='Color Verde (CSS)', default='#28a745')

    # ── ZONA AMARILLA ─────────────────────────────────────────────────────────
    warning_label = fields.Char(string='Etiqueta Amarilla', default='Próximo a vencer', required=True)
    warning_icon = fields.Char(string='Ícono Amarillo (FA)', default='fa-clock-o')
    warning_color = fields.Char(string='Color Amarillo (CSS)', default='#ffc107')
    warning_threshold_pct = fields.Float(
        string='Umbral Amarillo (%)', default=25.0,
        help='Cuando el tiempo restante sea menor a este % del total SLA, el semáforo cambia a amarillo.',
    )
    warning_threshold_hours = fields.Float(
        string='Umbral Amarillo (horas absolutas)', default=0.0,
        help='Si > 0, pasa a amarillo cuando queden MENOS de estas horas.',
    )

    # ── ZONA ROJA ─────────────────────────────────────────────────────────────
    danger_label = fields.Char(string='Etiqueta Roja', default='SLA Vencido', required=True)
    danger_icon = fields.Char(string='Ícono Rojo (FA)', default='fa-exclamation-circle')
    danger_color = fields.Char(string='Color Rojo (CSS)', default='#dc3545')

    # ── ZONA GRIS (cerrado) ───────────────────────────────────────────────────
    closed_label = fields.Char(string='Etiqueta Cerrado', default='Cerrado', required=True)
    closed_icon = fields.Char(string='Ícono Cerrado (FA)', default='fa-check')
    closed_color = fields.Char(string='Color Cerrado (CSS)', default='#6c757d')

    # ── SLA POR PRIORIDAD (campos legado — compatibilidad con ticket) ─────────
    sla_hours_critical = fields.Float(string='SLA Crítica (horas)', default=4.0, required=True)
    sla_hours_high = fields.Float(string='SLA Alta (horas)', default=24.0, required=True)
    sla_hours_medium = fields.Float(string='SLA Media (horas)', default=48.0, required=True)
    sla_hours_low = fields.Float(string='SLA Baja (horas)', default=72.0, required=True)

    # ── SLA POR PRIORIDAD (dinámico) ──────────────────────────────────────────
    priority_sla_ids = fields.One2many(
        comodel_name='helpdesk.priority.sla',
        inverse_name='config_id',
        string='Prioridades SLA',
        help='Niveles de prioridad configurables: color, nombre y horas límite.',
    )

    # ── CRON SETTINGS ─────────────────────────────────────────────────────────
    escalate_on_expire = fields.Boolean(
        string='Escalar automáticamente al vencer SLA', default=True,
        help='El cron moverá los tickets vencidos a la etapa "En Espera".',
    )
    notify_on_warning = fields.Boolean(
        string='Notificar al responsable cuando entre en zona amarilla', default=True,
    )

    default_ticket_sla_days = fields.Integer(
        string='Dias SLA por defecto en tickets',
        compute='_compute_default_ticket_sla_days',
        inverse='_inverse_default_ticket_sla_days',
        store=False,
    )

    # ── MÉTODOS HELPER ────────────────────────────────────────────────────────
    @api.model
    def _create_default_priorities(self, config_id):
        """Crear las 5 prioridades SLA por defecto de forma segura."""
        import logging
        _logger = logging.getLogger(__name__)
        
        PrioritySla = self.env['helpdesk.priority.sla'].sudo()
        
        existing = PrioritySla.search([('config_id', '=', config_id)])
        if len(existing) >= 5:
            _logger.warning(f"Config {config_id} ya tiene {len(existing)} prioridades, skipping")
            return
        
        for seq, nombre, color, horas, atencion in PRIORIDADES_DEFAULT:
            try:
                exists = PrioritySla.search_count([
                    ('config_id', '=', config_id),
                    ('sequence', '=', seq),
                ])
                
                if not exists:
                    PrioritySla.create({
                        'config_id': config_id,
                        'sequence': seq,
                        'name': nombre,
                        'color': color,
                        'hours_limit': horas,
                        'attention_time': atencion,
                    })
                    _logger.info(f"✓ Prioridad '{nombre}' creada para config {config_id}")
                
            except Exception as e:
                _logger.error(f"✗ Error al crear prioridad '{nombre}': {str(e)}")

    # ── SINGLETON ─────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        """Crear configuración. Las prioridades se crean SOLO si no existen."""
        configs = super().create(vals_list)
        
        # Crear prioridades SOLO si no existen
        for config in configs:
            priority_count = self.env['helpdesk.priority.sla'].search_count([
                ('config_id', '=', config.id)
            ])
            
            # Solo crear si NO hay prioridades
            if priority_count == 0:
                self._create_default_priorities(config.id)
        
        return configs

    @api.model
    def get_config(self):
        """Obtener la única configuración SLA."""
        config = self.search([], limit=1)
        if not config:
            config = self.sudo().create({'name': 'Configuración SLA'})
        return config

    @api.model
    def action_open_config(self):
        """
        Abrir la configuración SLA singleton, garantizando que exista y esté cargada.
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            config = self.get_config()
            self._ensure_default_priorities(config.id)
            _logger.info(f"✓ HelpdeskSlaConfig abierto: ID {config.id}")
            
            return {
                'type': 'ir.actions.act_window',
                'name': '🚦 Semáforo SLA',
                'res_model': 'helpdesk.sla.config',
                'view_mode': 'form',
                'res_id': config.id,
                'target': 'current',
            }
        except Exception as e:
            _logger.error(f"✗ Error en action_open_config: {str(e)}")
            raise
    
    def _ensure_default_priorities(self, config_id):
        """Solo crear prioridades si no existe ninguna."""
        import logging
        _logger = logging.getLogger(__name__)
        
        priority_count = self.env['helpdesk.priority.sla'].search_count([
            ('config_id', '=', config_id)
        ])
        
        if priority_count == 0:
            _logger.warning(f"Config {config_id} no tiene prioridades. Creando 5 por defecto...")
            try:
                self._create_default_priorities(config_id)
                _logger.info(f"✓ Prioridades SLA creadas para config {config_id}")
            except Exception as e:
                _logger.error(f"✗ Error creando prioridades: {str(e)}")

    def action_refresh_data(self):
        """Recargar los datos desde BD y reconstruir prioridades si es necesario."""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Recargar desde BD (invalidar caché y re-buscar)
            self.env.invalidate_all()
            self = self.browse(self.id)
            
            # Validar/recrear prioridades si es necesario
            self._ensure_default_priorities(self.id)
            
            _logger.info(f"✓ Datos actualizados para config {self.id}")
            
            # Retornar una acción para recargar la vista
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            _logger.error(f"✗ Error al actualizar datos: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✗ Error',
                    'message': f'Error al actualizar datos: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                },
            }

    def action_regenerate_priorities(self):
        """Restablecer toda la configuración a valores por defecto."""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Limpiar todas las prioridades
            self.priority_sla_ids.sudo().unlink()
            
            # Recrear las 5 prioridades por defecto
            self._create_default_priorities(self.id)
            
            # Restablecer etiquetas y colores
            self.write({
                'ok_label': 'En tiempo',
                'ok_color': '#28a745',
                'warning_label': 'Próximo a vencer',
                'warning_color': '#ffc107',
                'warning_threshold_pct': 25.0,
                'warning_threshold_hours': 0.0,
                'danger_label': 'SLA Vencido',
                'danger_color': '#dc3545',
                'closed_label': 'Cerrado',
                'closed_color': '#6c757d',
                'sla_hours_critical': 4.0,
                'sla_hours_high': 24.0,
                'sla_hours_medium': 48.0,
                'sla_hours_low': 72.0,
                'escalate_on_expire': True,
                'notify_on_warning': True,
            })
            
            _logger.info(f"✓ Configuración restablecida para config {self.id}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            _logger.error(f"✗ Error al restablecer configuración: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✗ Error',
                    'message': f'Error al restablecer configuración: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                },
            }

    @api.model
    def get_sla_hours_by_priority(self, priority):
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
