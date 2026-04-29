# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class DepartmentModuleAccess(models.Model):
    """
    Controla la visibilidad de menús/módulos de Odoo para un departamento.
    Funciona junto con la política del departamento (whitelist/blacklist).
    """
    _name = 'department.module.access'
    _description = 'Visibilidad de Módulo por Departamento'
    _order = 'department_id, menu_id'

    def _default_access_type(self):
        dept_id = self.env.context.get('default_department_id')
        if dept_id:
            dept = self.env['hr.department'].browse(dept_id)
            if dept.exists() and dept.access_policy == 'blacklist':
                return 'hidden'
        return 'visible'

    def _access_type_for_department(self, department_id):
        if not department_id:
            return 'visible'
        dept = self.env['hr.department'].browse(department_id)
        if dept.exists() and dept.access_policy == 'blacklist':
            return 'hidden'
        return 'visible'

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        required=True,
        ondelete='cascade',
        index=True,
    )

    menu_id = fields.Many2one(
        'ir.ui.menu',
        string='Módulo / Menú / Sección',
        required=True,
        ondelete='cascade',
        help='Puede ser un módulo principal o un submenú específico para controlar solo una parte.',
    )
    menu_name = fields.Char(
        string='Nombre del Módulo',
        compute='_compute_menu_name',
        store=True,
    )

    access_type = fields.Selection(
        selection=[
            ('visible', 'Visible (Permitido)'),
            ('hidden',  'Oculto (Bloqueado)'),
        ],
        string='Tipo de Acceso',
        default=_default_access_type,
        required=True,
    )

    include_children = fields.Boolean(
        string='Incluir Submenús',
        default=True,
        help='Si está activo, la regla también aplica a todos los submenús de esta sección.',
    )

    active = fields.Boolean(default=True)
    notes  = fields.Char(string='Observaciones')

    _sql_constraints = [
        ('dept_menu_unique', 'UNIQUE(department_id, menu_id)',
         'Ya existe una regla para este menú en este departamento.'),
    ]

    @api.depends('menu_id', 'menu_id.complete_name')
    def _compute_menu_name(self):
        for rec in self:
            rec.menu_name = rec.menu_id.complete_name if rec.menu_id else ''

    @api.onchange('department_id', 'menu_id')
    def _onchange_default_hidden_blacklist(self):
        for rec in self:
            if rec.department_id and rec.department_id.access_policy == 'blacklist':
                rec.access_type = 'hidden'

    def _clear_menu_cache(self):
        self.env.registry.clear_cache()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('access_type'):
                vals['access_type'] = self._access_type_for_department(vals.get('department_id'))
        records = super().create(vals_list)
        records._clear_menu_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'department_id', 'menu_id', 'access_type', 'include_children', 'active'} & set(vals):
            self._clear_menu_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res
