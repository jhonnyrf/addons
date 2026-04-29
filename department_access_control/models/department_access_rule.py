# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DepartmentAccessRule(models.Model):
    """
    Regla de acceso a un modelo de datos específico o a un módulo completo para un departamento.
    Define qué operaciones CRUD puede hacer el departamento sobre ese modelo o módulo.
    """
    _name = 'department.access.rule'
    _description = 'Regla de Acceso a Modelo o Módulo por Departamento'
    _order = 'department_id, rule_type, model_id, menu_id'

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        required=True,
        ondelete='cascade',
        index=True,
    )

    rule_type = fields.Selection(
        selection=[
            ('modelo',  'Modelo Individual'),
            ('modulo',  'Módulo / Sección'),
        ],
        string='Tipo de Regla',
        default='modelo',
        required=True,
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Modelo / Objeto',
        ondelete='cascade',
        help='El modelo de datos sobre el que aplica esta regla (ej: Factura, Empleado, etc.)',
    )
    model_name = fields.Char(related='model_id.name', string='Nombre del Modelo', readonly=True)
    model_model = fields.Char(related='model_id.model', string='Referencia Técnica', readonly=True)

    menu_id = fields.Many2one(
        'ir.ui.menu',
        string='Módulo / Menú / Sección',
        ondelete='cascade',
        help='El módulo o sección sobre el que aplica esta regla. Se aplicará a todos sus modelos.',
    )
    menu_name = fields.Char(
        string='Nombre del Módulo',
        compute='_compute_menu_name',
        store=True,
    )
    include_submenu_models = fields.Boolean(
        string='Incluir Submenús',
        default=True,
        help='Si está activo, la regla se aplica a los modelos de los submenús también.',
    )

    access_level = fields.Selection(
        selection=[
            ('readonly',  'Solo Lectura'),
            ('write',     'Lectura y Escritura'),
            ('full',      'Acceso Completo'),
            ('noaccess',  'Sin Acceso'),
            ('custom',    'Personalizado'),
        ],
        string='Nivel de Acceso',
        default='readonly',
        required=True,
    )

    perm_read   = fields.Boolean(string='Leer',      default=True)
    perm_write  = fields.Boolean(string='Modificar', default=False)
    perm_create = fields.Boolean(string='Crear',     default=False)
    perm_unlink = fields.Boolean(string='Eliminar',  default=False)

    active = fields.Boolean(default=True)
    notes  = fields.Char(string='Observaciones')

    _sql_constraints = [
        ('dept_model_unique', 'UNIQUE(department_id, model_id) WHERE rule_type = %s',
         'Ya existe una regla para este modelo en este departamento.'),
        ('dept_menu_unique', 'UNIQUE(department_id, menu_id) WHERE rule_type = %s',
         'Ya existe una regla para este módulo en este departamento.'),
    ]

    @api.depends('menu_id', 'menu_id.complete_name')
    def _compute_menu_name(self):
        for rec in self:
            rec.menu_name = rec.menu_id.complete_name if rec.menu_id else ''

    @api.onchange('rule_type')
    def _onchange_rule_type(self):
        """Limpiar campos según tipo de regla seleccionado."""
        if self.rule_type == 'modelo':
            self.menu_id = False
            self.include_submenu_models = False
        elif self.rule_type == 'modulo':
            self.model_id = False

    def _infer_rule_type(self, vals):
        """Deriva el tipo de regla a partir de los campos informados."""
        if vals.get('rule_type'):
            return vals

        inferred_vals = dict(vals)
        if inferred_vals.get('menu_id') and not inferred_vals.get('model_id'):
            inferred_vals['rule_type'] = 'modulo'
        elif inferred_vals.get('model_id') and not inferred_vals.get('menu_id'):
            inferred_vals['rule_type'] = 'modelo'

        return inferred_vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._infer_rule_type(vals) for vals in vals_list]
        return super().create(vals_list)

    def write(self, vals):
        vals = self._infer_rule_type(vals)
        return super().write(vals)

    @api.constrains('rule_type', 'model_id', 'menu_id')
    def _check_rule_consistency(self):
        for rec in self:
            if rec.rule_type == 'modelo' and not rec.model_id:
                raise ValidationError(
                    _('Debes seleccionar un Modelo cuando el tipo de regla es "Modelo Individual".')
                )
            if rec.rule_type == 'modulo' and not rec.menu_id:
                raise ValidationError(
                    _('Debes seleccionar un Módulo cuando el tipo de regla es "Módulo / Sección".')
                )

    @api.onchange('access_level')
    def _onchange_access_level(self):
        mapping = {
            'readonly':  (True,  False, False, False),
            'write':     (True,  True,  True,  False),
            'full':      (True,  True,  True,  True),
            'noaccess':  (False, False, False, False),
        }
        if self.access_level in mapping:
            r, w, c, u = mapping[self.access_level]
            self.perm_read   = r
            self.perm_write  = w
            self.perm_create = c
            self.perm_unlink = u

    @api.onchange('perm_read', 'perm_write', 'perm_create', 'perm_unlink')
    def _onchange_perms(self):
        combo = (self.perm_read, self.perm_write, self.perm_create, self.perm_unlink)
        mapping = {
            (True,  False, False, False): 'readonly',
            (True,  True,  True,  False): 'write',
            (True,  True,  True,  True):  'full',
            (False, False, False, False): 'noaccess',
        }
        self.access_level = mapping.get(combo, 'custom')

    @api.constrains('perm_read', 'perm_write', 'perm_create', 'perm_unlink')
    def _check_perms(self):
        for rec in self:
            label = rec.model_name or rec.menu_name or 'Esta regla'
            if (rec.perm_write or rec.perm_create or rec.perm_unlink) and not rec.perm_read:
                raise ValidationError(_(
                    '"%s" debe tener permiso de lectura si tiene otros permisos activos.'
                ) % label)

    def get_affected_models(self):
        """
        Retorna los modelos afectados por esta regla.
        Si es regla por modelo, devuelve ese modelo.
        Si es por módulo, devuelve todos los modelos del módulo/sección.
        """
        self.ensure_one()
        if self.rule_type == 'modelo':
            return self.model_id
        
        # Para reglas por módulo, buscar modelos del módulo
        if self.rule_type == 'modulo' and self.menu_id:
            menu_ids = [self.menu_id.id]
            if self.include_submenu_models:
                menu_ids = self.env['ir.ui.menu'].search([
                    ('id', 'child_of', self.menu_id.id)
                ]).ids

            # Buscar acciones de ventana del menú que apunten a modelos
            ir_model_ids = self.env['ir.actions.act_window'].search([
                ('res_model', '!=', False),
            ]).filtered(lambda a: a.res_model not in ['ir.ui.menu', 'ir.model', 'ir.filters']).mapped('res_model')

            # Devolver los modelos
            return self.env['ir.model'].search([('model', 'in', ir_model_ids)])
        
        return self.env['ir.model']
