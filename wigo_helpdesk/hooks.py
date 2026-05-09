# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

PRIORIDADES_DEFAULT = [
    (10, 'Muy Alta',  '#e53935', 24.0,  'Inmediato (30 min. Después de notificación ya se debe estar atendiendo)'),
    (20, 'Alta',      '#f57c00', 72.0,  'Inmediato según orden de prelación'),
    (30, 'Media',     '#fdd835', 72.0,  'Priorizado según orden de prelación'),
    (40, 'Baja',      '#8bc34a', 48.0,  'Priorizado según orden de prelación'),
    (50, 'Crítica',   '#7b0000',  6.0,  'Inmediato (15 min. Después de notificación ya se debe estar atendiendo)'),
]


def post_init_hook(env_or_cr, registry=None):
    """Compat post-init hook (soporta firma nueva env y antigua cr, registry)."""
    import logging
    _logger = logging.getLogger(__name__)
    
    if registry is None and hasattr(env_or_cr, 'cr'):
        env = api.Environment(env_or_cr.cr, SUPERUSER_ID, dict(getattr(env_or_cr, 'context', {}) or {}))
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})

    try:
        # ── Limpieza original ────────────────────────────────────────────────────
        escalated_stage = env.ref('wigo_helpdesk.stage_escalated', raise_if_not_found=False)
        waiting_stage = env['helpdesk.stage'].search([('name', '=', 'En Espera')], limit=1)

        if escalated_stage:
            if waiting_stage and escalated_stage.id != waiting_stage.id:
                env['helpdesk.ticket'].sudo().search([('stage_id', '=', escalated_stage.id)]).write({
                    'stage_id': waiting_stage.id,
                })
            escalated_stage.sudo().unlink()
        
        _logger.info("✓ Limpieza de etapas completada")
    except Exception as e:
        _logger.error(f"✗ Error en limpieza de etapas: {str(e)}")

    try:
        # ── Limpieza de duplicados de prioridades ──────────────────────────────
        _logger.info("Limpiando duplicados de prioridades SLA...")
        
        # Contar prioridades por config y nombre
        PrioritySla = env['helpdesk.priority.sla'].sudo()
        all_priorities = PrioritySla.search([])
        
        # Agrupar por config_id y name para encontrar duplicados
        priority_map = {}
        duplicates_to_delete = []
        
        for priority in all_priorities:
            key = (priority.config_id.id, priority.name, priority.sequence)
            if key in priority_map:
                # Este es un duplicado
                duplicates_to_delete.append(priority.id)
                _logger.warning(f"Duplicado encontrado: {priority.name} (ID: {priority.id})")
            else:
                priority_map[key] = priority.id
        
        if duplicates_to_delete:
            PrioritySla.browse(duplicates_to_delete).unlink()
            _logger.info(f"✓ Eliminados {len(duplicates_to_delete)} duplicados de prioridades")
        else:
            _logger.info("✓ No hay duplicados de prioridades")
    
    except Exception as e:
        _logger.error(f"✗ Error en limpieza de duplicados: {str(e)}")

    try:
        # ── Seed de prioridades SLA ───────────────────────────────────────────────
        config = env['helpdesk.sla.config'].sudo().get_config()
        priority_count = env['helpdesk.priority.sla'].search_count([
            ('config_id', '=', config.id)
        ])
        
        if priority_count == 0:
            _logger.info("Creando prioridades SLA por defecto...")
            for seq, nombre, color, horas, atencion in PRIORIDADES_DEFAULT:
                try:
                    env['helpdesk.priority.sla'].sudo().create({
                        'config_id': config.id,
                        'sequence': seq,
                        'name': nombre,
                        'color': color,
                        'hours_limit': horas,
                        'attention_time': atencion,
                    })
                    _logger.info(f"  ✓ Prioridad '{nombre}' creada")
                except Exception as e:
                    _logger.error(f"  ✗ Error al crear prioridad '{nombre}': {str(e)}")
            
            _logger.info("✓ Prioridades SLA creadas")
        elif priority_count == 5:
            _logger.info(f"✓ Ya existen {priority_count} prioridades SLA (correcto)")
        else:
            _logger.warning(f"⚠ Config tiene {priority_count} prioridades (esperaba 5). Recreando...")
            try:
                old = env['helpdesk.priority.sla'].sudo().search([
                    ('config_id', '=', config.id)
                ])
                if old:
                    old.unlink()
                
                for seq, nombre, color, horas, atencion in PRIORIDADES_DEFAULT:
                    env['helpdesk.priority.sla'].sudo().create({
                        'config_id': config.id,
                        'sequence': seq,
                        'name': nombre,
                        'color': color,
                        'hours_limit': horas,
                        'attention_time': atencion,
                    })
                
                _logger.info(f"✓ Prioridades SLA recreadas correctamente")
            except Exception as e:
                _logger.error(f"✗ Error recreando prioridades: {str(e)}")
    
    except Exception as e:
        _logger.error(f"✗ Error en seed de prioridades SLA: {str(e)}")
