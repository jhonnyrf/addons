# -*- coding: utf-8 -*-
from odoo import _, models, SUPERUSER_ID
from odoo.exceptions import AccessError


class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    def _get_department_employee_for_user(self):
        """Return the active employee subject to department access rules."""
        if self.env.uid == SUPERUSER_ID:
            return False

        employees = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.env.uid),
            ('use_department_access', '=', True),
            ('department_id', '!=', False),
            ('department_id.restrict_access', '=', True),
        ])
        if not employees:
            return False

        current_company = self.env.company
        company_match = employees.filtered(lambda e: e.company_id == current_company)
        return (company_match or employees)[:1]

    @staticmethod
    def _is_operation_allowed(rule, operation):
        mapping = {
            'read': 'perm_read',
            'write': 'perm_write',
            'create': 'perm_create',
            'unlink': 'perm_unlink',
        }
        field_name = mapping.get(operation)
        return bool(field_name and getattr(rule, field_name))

    def check(self, model_name, mode='read', raise_exception=True, operation=None, **kwargs):
        # Odoo core calls this method with positional mode; keep backward compatibility
        # with custom callers that may pass operation as keyword.
        op = kwargs.get('operation') or operation or mode

        # Respect native ACLs first.
        try:
            allowed = super().check(model_name, op, raise_exception=raise_exception)
        except TypeError:
            try:
                allowed = super().check(model_name, op, raise_exception)
            except TypeError:
                allowed = super().check(model_name, op)
        if not allowed:
            return allowed

        # Bypass for superuser and module managers.
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group(
            'department_access_control.group_department_access_manager'
        ):
            return allowed

        employee = self._get_department_employee_for_user()
        if not employee:
            return allowed

        # Buscar regla por modelo específico
        rule = self.env['department.access.rule'].sudo().search([
            ('department_id', '=', employee.department_id.id),
            ('active', '=', True),
            ('rule_type', '=', 'modelo'),
            ('model_model', '=', model_name),
        ], limit=1)

        # Si no hay regla por modelo, buscar por módulo
        if not rule:
            # Lookup técnico: no debe depender de permisos del usuario final.
            model_obj = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
            if model_obj:
                # Buscar todas las reglas por módulo del departamento
                menu_rules = self.env['department.access.rule'].sudo().search([
                    ('department_id', '=', employee.department_id.id),
                    ('active', '=', True),
                    ('rule_type', '=', 'modulo'),
                ])
                
                # Encontrar la primera regla que aplique a este modelo
                for menu_rule in menu_rules:
                    affected_models = menu_rule.get_affected_models()
                    if model_obj in affected_models:
                        rule = menu_rule
                        break

        if not rule:
            return allowed

        if self._is_operation_allowed(rule, op):
            return allowed

        if raise_exception:
            label = rule.model_name or rule.menu_name or model_name
            raise AccessError(_(
                'Operación no permitida por la política de acceso del departamento.\n'
                'Recurso: %s\n'
                'Operación: %s\n'
                'Departamento: %s'
            ) % (label, op, employee.department_id.name))

        return False
