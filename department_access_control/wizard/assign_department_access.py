# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardAssignDepartmentAccess(models.TransientModel):
    """
    Wizard para aplicar en masa los permisos del departamento
    a los empleados, o asignar permisos individuales rápidamente.
    """
    _name = 'wizard.assign.department.access'
    _description = 'Asistente de Asignación de Permisos'

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        required=True,
    )
    apply_to = fields.Selection(
        selection=[
            ('all_employees', 'Todos los empleados del departamento'),
            ('selected_employees', 'Empleados seleccionados'),
        ],
        string='Aplicar a',
        default='all_employees',
        required=True,
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Empleados',
        domain="[('department_id', '=', department_id)]",
    )
    action_type = fields.Selection(
        selection=[
            ('enable_dept_perms', 'Activar permisos de departamento'),
            ('disable_dept_perms', 'Desactivar permisos de departamento'),
            ('reset_individual', 'Limpiar permisos individuales'),
        ],
        string='Acción',
        default='enable_dept_perms',
        required=True,
    )

    # Info calculada
    employee_count = fields.Integer(
        compute='_compute_employee_count',
        string='Empleados afectados',
    )
    department_has_restrictions = fields.Boolean(
        related='department_id.restrict_access',
        string='Tiene restricciones',
    )

    @api.depends('department_id', 'apply_to', 'employee_ids')
    def _compute_employee_count(self):
        for wiz in self:
            if wiz.apply_to == 'all_employees' and wiz.department_id:
                wiz.employee_count = self.env['hr.employee'].search_count([
                    ('department_id', '=', wiz.department_id.id)
                ])
            else:
                wiz.employee_count = len(wiz.employee_ids)

    def action_apply(self):
        self.ensure_one()

        if self.apply_to == 'all_employees':
            employees = self.env['hr.employee'].search([
                ('department_id', '=', self.department_id.id)
            ])
        else:
            employees = self.employee_ids

        if not employees:
            raise UserError(_('No hay empleados para procesar.'))

        if self.action_type == 'enable_dept_perms':
            employees.write({'use_department_access': True})
            msg = _('%d empleados ahora usan permisos del departamento.') % len(employees)

        elif self.action_type == 'disable_dept_perms':
            employees.write({'use_department_access': False})
            msg = _('%d empleados ya no usan permisos del departamento.') % len(employees)

        elif self.action_type == 'reset_individual':
            # Elimina todos los permisos individuales
            individual_access = self.env['department.employee.module.access'].search([
                ('employee_id', 'in', employees.ids)
            ])
            individual_access.unlink()
            msg = _('Permisos individuales eliminados para %d empleados.') % len(employees)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Permisos Actualizados'),
                'message': msg,
                'type': 'success',
                'sticky': False,
            }
        }
