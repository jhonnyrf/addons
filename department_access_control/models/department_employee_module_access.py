# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class DepartmentEmployeeModuleAccess(models.Model):
    """
    Override individual de visibilidad de módulos para un empleado específico.
    Permite dar o quitar acceso a menús concretos, sobreescribiendo la política del departamento.
    """
    _name = 'department.employee.module.access'
    _description = 'Permiso Individual de Módulo para Empleado'
    _order = 'employee_id, menu_id'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        ondelete='cascade',
        index=True,
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Departamento',
        store=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        related='employee_id.user_id',
        string='Usuario del Sistema',
        store=True,
        readonly=True,
    )

    menu_id = fields.Many2one(
        'ir.ui.menu',
        string='Módulo / Menú / Sección',
        required=True,
        ondelete='cascade',
    )
    menu_name = fields.Char(
        string='Nombre del Módulo',
        compute='_compute_menu_name',
        store=True,
    )

    access_type = fields.Selection(
        selection=[
            ('visible', 'Visible (Permitir acceso)'),
            ('hidden',  'Oculto (Bloquear acceso)'),
        ],
        string='Tipo de Acceso',
        default='visible',
        required=True,
    )

    include_children = fields.Boolean(
        string='Incluir Submenús',
        default=True,
        help='Si está activo, la regla también aplica a los submenús de esta sección.',
    )

    override_department = fields.Boolean(
        string='Sobreescribe al Departamento',
        default=True,
        help='Si está activo, este permiso prevalece sobre la configuración del departamento.',
    )

    active = fields.Boolean(default=True)
    reason = fields.Char(string='Razón / Justificación')

    _sql_constraints = [
        ('emp_menu_unique', 'UNIQUE(employee_id, menu_id)',
         'Ya existe un permiso individual para este menú en este empleado.'),
    ]

    @api.depends('menu_id', 'menu_id.complete_name')
    def _compute_menu_name(self):
        for rec in self:
            rec.menu_name = rec.menu_id.complete_name if rec.menu_id else ''

    def _clear_menu_cache(self):
        self.env.registry.clear_cache()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._clear_menu_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'employee_id', 'menu_id', 'access_type', 'include_children', 'override_department', 'active'} & set(vals):
            self._clear_menu_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res
