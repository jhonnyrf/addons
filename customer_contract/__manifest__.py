# -*- coding: utf-8 -*-
{
    'name': 'Contratos de Clientes',
    'version': '19.0.1.0.0',
    'summary': 'Gestión de contratos de clientes para servicios de internet',
    'description': """
        Módulo para la gestión completa de contratos de clientes.
        Permite registrar datos personales, asignar planes de internet,
        generar contratos con numeración automática y registrar cambios de plan
        con historial completo (COM-11).
    """,
    'author': 'Tu Empresa',
    'category': 'Sales/Sales',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'wigo_planes', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/cron.xml',
        'views/customer_contract_plan_wizard.xml',
        'views/customer_contract_views.xml',
        'views/res_partner_contract_views.xml',
        'views/customer_contract_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'customer_contract/static/src/js/contract_clipboard.js',
            'customer_contract/static/src/css/contract_clipboard.css',
            'customer_contract/static/src/scss/contract_clipboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
