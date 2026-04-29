# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrEmployee(models.Model):
    """Extiende hr.employee para gestionar permisos individuales adicionales."""
    _inherit = 'hr.employee'

    # Permisos individuales de módulos (override del departamento)
    individual_module_access_ids = fields.One2many(
        'department.employee.module.access',
        'employee_id',
        string='Acceso Individual a Módulos',
        help='Permisos individuales que sobreescriben los del departamento',
    )

    use_department_access = fields.Boolean(
        string='Usar Permisos del Departamento',
        default=True,
        help='Si está activo, hereda los permisos configurados en su departamento',
    )

    # Resumen de permisos efectivos (campo calculado informativo)
    access_summary = fields.Text(
        string='Resumen de Accesos',
        compute='_compute_access_summary',
        help='Resumen de los permisos efectivos para este empleado',
    )

    individual_module_count = fields.Integer(
        compute='_compute_individual_module_count',
        string='Módulos Individuales',
    )

    @api.depends('individual_module_access_ids')
    def _compute_individual_module_count(self):
        for emp in self:
            emp.individual_module_count = len(emp.individual_module_access_ids)

    @api.depends(
        'department_id',
        'department_id.restrict_access',
        'department_id.access_rule_ids',
        'department_id.module_access_ids',
        'individual_module_access_ids',
        'use_department_access',
    )
    def _compute_access_summary(self):
        for emp in self:
            lines = []
            dept = emp.department_id

            if emp.use_department_access and dept and dept.restrict_access:
                lines.append(f"📁 Departamento: {dept.name}")
                lines.append(f"   Política: {'Lista Blanca' if dept.access_policy == 'whitelist' else 'Lista Negra'}")

                rules = dept.get_effective_access_rules()
                if rules:
                    lines.append(f"   Reglas de datos: {len(rules)} configuradas")

                module_rules = dept.module_access_ids.filtered('active')
                visible = module_rules.filtered(lambda m: m.access_type == 'visible')
                hidden = module_rules.filtered(lambda m: m.access_type == 'hidden')
                if visible:
                    lines.append(f"   Módulos visibles: {', '.join(visible.mapped('menu_name'))}")
                if hidden:
                    lines.append(f"   Módulos ocultos: {', '.join(hidden.mapped('menu_name'))}")
            else:
                lines.append("ℹ️ Sin restricciones de departamento aplicadas")

            if emp.individual_module_access_ids:
                lines.append("\n👤 Permisos Individuales:")
                for acc in emp.individual_module_access_ids.filtered('active'):
                    icon = "✅" if acc.access_type == 'visible' else "🚫"
                    lines.append(f"   {icon} {acc.menu_id.name}")

            emp.access_summary = '\n'.join(lines) if lines else 'Sin configuración especial'

    def action_view_individual_module_access(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Acceso Individual a Módulos — %s') % self.name,
            'res_model': 'department.employee.module.access',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def get_effective_menu_ids(self):
        """
        Calcula los menús efectivos para este empleado,
        combinando permisos del departamento con los individuales.
        """
        self.ensure_one()
        all_menus = self.env['ir.ui.menu'].search([])

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

        # Permisos base del departamento
        if self.use_department_access and self.department_id:
            base_ids = set(self.department_id.get_allowed_menu_ids())
        else:
            base_ids = set(all_menus.ids)

        # Aplicar overrides individuales
        for acc in self.individual_module_access_ids.filtered(
            lambda a: a.active and a.override_department
        ):
            if acc.access_type == 'visible':
                base_ids.update(_menu_scope_ids(acc.menu_id, acc.include_children))
            elif acc.access_type == 'hidden':
                base_ids.difference_update(_menu_scope_ids(acc.menu_id, acc.include_children))

        return list(_add_ancestors(base_ids))

    def write(self, vals):
        res = super().write(vals)
        if {'department_id', 'use_department_access', 'user_id'} & set(vals):
            self.env.registry.clear_cache()
        return res
