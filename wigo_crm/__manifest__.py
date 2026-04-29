{
    'name': "Wigo CRM",
    'summary': "Personalización del CRM para Wigo",
    'description': """
Módulo para personalizar el CRM de Odoo según los requerimientos de Wigo.
    """,
    'author': "Wigo",
    'website': "",
    'category': 'Sales',
    'version': '1.0',
    'license': 'LGPL-3',
    # ← Cambiado de 'wigo_plan' a 'wigo_planes' (módulo unificado)
    'depends': ['base', 'crm', 'wigo_planes', 'customer_contract', 'wigo_ftth'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_form_views.xml',
        'views/crm_lead_adjustments_views.xml',
        'views/crm_lead_kanban_views.xml',
        'views/crm_menu_views.xml',
        'views/crm_stage_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wigo_crm/static/src/js/wigo_crm.js',
            'wigo_crm/static/src/css/wigo_crm.css',
        ],
    },
    'installable': True,
    'application': True,
}
