# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrDepartment(models.Model):
    """Extiende hr.department para gestionar reglas de acceso y módulos visibles."""
    _inherit = 'hr.department'

    # Reglas de acceso a modelos
    access_rule_ids = fields.One2many(
        'department.access.rule',
        'department_id',
        string='Reglas de Acceso a Datos',
    )
    access_rule_count = fields.Integer(
        compute='_compute_access_rule_count',
        string='Nº Reglas',
    )

    # Acceso a módulos/menús
    module_access_ids = fields.One2many(
        'department.module.access',
        'department_id',
        string='Acceso a Módulos',
    )
    module_access_count = fields.Integer(
        compute='_compute_module_access_count',
        string='Nº Módulos',
    )

    # Configuración general
    restrict_access = fields.Boolean(
        string='Activar Restricciones de Acceso',
        default=False,
        help='Si está activo, se aplican las reglas de acceso configuradas para este departamento',
    )
    access_policy = fields.Selection(
        selection=[
            ('whitelist', 'Lista Blanca (Solo módulos permitidos son visibles)'),
            ('blacklist', 'Lista Negra (Todos los módulos excepto los bloqueados)'),
        ],
        string='Política de Acceso a Módulos',
        default='blacklist',
        help='Whitelist: solo ve los módulos que se le permitan explícitamente.\n'
             'Blacklist: ve todo excepto los módulos que se bloqueen.',
    )

    @api.depends('access_rule_ids')
    def _compute_access_rule_count(self):
        for dept in self:
            dept.access_rule_count = len(dept.access_rule_ids)

    @api.depends('module_access_ids')
    def _compute_module_access_count(self):
        for dept in self:
            dept.module_access_count = len(dept.module_access_ids)

    def action_view_access_rules(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reglas de Acceso — %s') % self.name,
            'res_model': 'department.access.rule',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }

    def action_view_module_access(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Acceso a Módulos — %s') % self.name,
            'res_model': 'department.module.access',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }

    def action_apply_access_to_employees(self):
        """Abre el wizard para aplicar permisos a todos los empleados del departamento."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Aplicar Permisos a Empleados'),
            'res_model': 'wizard.assign.department.access',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_department_id': self.id,
                'default_apply_to': 'all_employees',
            },
        }

    def get_effective_access_rules(self):
        """Retorna las reglas de acceso activas del departamento."""
        self.ensure_one()
        return self.access_rule_ids.filtered(lambda r: r.active)

    def get_allowed_menu_ids(self):
        """
        Retorna los IDs de menús permitidos según la política del departamento.
        """
        self.ensure_one()
        all_menus = self.env['ir.ui.menu'].search([])

        if not self.restrict_access:
            return all_menus.ids

        def _menu_scope_ids(menu_rec, include_children):
            if include_children:
                return set(self.env['ir.ui.menu'].search([('id', 'child_of', menu_rec.id)]).ids)
            return {menu_rec.id}

        def _add_ancestors(menu_ids):
            if not menu_ids:
                return set()
            result = set(menu_ids)
            to_process = self.env['ir.ui.menu'].browse(list(menu_ids))
            while to_process:
                parents = to_process.mapped('parent_id').filtered(lambda p: p.id and p.id not in result)
                if not parents:
                    break
                parent_ids = set(parents.ids)
                result.update(parent_ids)
                to_process = parents
            return result

        rules = self.module_access_ids.filtered(lambda m: m.active and m.menu_id)

        if self.access_policy == 'whitelist':
            # Solo ve los menús marcados como visibles (y opcionalmente sus submenús).
            allowed_ids = set()
            for rule in rules.filtered(lambda r: r.access_type == 'visible'):
                allowed_ids.update(_menu_scope_ids(rule.menu_id, rule.include_children))

            # En whitelist hay que incluir ancestros para no romper la navegación del árbol.
            return list(_add_ancestors(allowed_ids))
        else:  # blacklist
            # Ve todo excepto los menús bloqueados (y opcionalmente sus submenús).
            blocked_ids = set()
            for rule in rules.filtered(lambda r: r.access_type == 'hidden'):
                blocked_ids.update(_menu_scope_ids(rule.menu_id, rule.include_children))

            return list(set(all_menus.ids) - blocked_ids)

    def write(self, vals):
        res = super().write(vals)
        if {'restrict_access', 'access_policy'} & set(vals):
            self.env.registry.clear_cache()
        return res
