# -*- coding: utf-8 -*-
{
    'name': 'Control de Acceso por Departamento',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Gestión de permisos de acceso por departamento y módulo',
    'description': """
Control de Acceso por Departamento
===================================
Permite configurar:
- Permisos de lectura/escritura/modificación/eliminación por departamento sobre modelos específicos
- Visibilidad de módulos y menús por departamento (lista blanca o lista negra)
- Permisos individuales por empleado que sobreescriben los del departamento
- Wizard para aplicar permisos en masa
    """,
    'author': 'Custom Module',
    'depends': ['base', 'hr', 'mail', 'web'],
    'data': [
        'security/department_access_security.xml',
        'security/ir.model.access.csv',
        'data/department_access_data.xml',
        'views/hr_department_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/department_access_rule_views.xml',
        'views/hr_employee_views.xml',
        'wizard/assign_department_access_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
