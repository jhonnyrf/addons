# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def post_init_hook(env_or_cr, registry=None):
    """Compat post-init hook.

    Odoo versions differ on the hook signature:
    - Newer versions call: post_init_hook(env)
    - Older versions call: post_init_hook(cr, registry)

    This implementation supports both.
    """
    if registry is None and hasattr(env_or_cr, 'cr'):
        # Called as post_init_hook(env)
        env = api.Environment(env_or_cr.cr, SUPERUSER_ID, dict(getattr(env_or_cr, 'context', {}) or {}))
    else:
        # Called as post_init_hook(cr, registry)
        cr = env_or_cr
        env = api.Environment(cr, SUPERUSER_ID, {})

    # =========================================================================
    # Limpieza original del módulo
    # =========================================================================
    escalated_stage = env.ref('wigo_helpdesk.stage_escalated', raise_if_not_found=False)
    waiting_stage = env['helpdesk.stage'].search([('name', '=', 'En Espera')], limit=1)

    if not escalated_stage:
        return

    if waiting_stage and escalated_stage.id != waiting_stage.id:
        env['helpdesk.ticket'].sudo().search([('stage_id', '=', escalated_stage.id)]).write({
            'stage_id': waiting_stage.id,
        })

    escalated_stage.sudo().unlink()