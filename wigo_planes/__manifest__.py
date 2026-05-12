# -*- coding: utf-8 -*-
{
    'name': 'Planes',
    'version': '19.0.1.0.1',
    'summary': 'Gestión de Planes de Internet y Promociones Wigo',
    'description': """
        Módulo unificado Wigo Planes.
        - Planes de internet (fibra, inalámbrico, cable) con vista kanban/lista/formulario.
        - Costos de instalación configurables.
        - Promociones: referidos, descuentos, mes gratis y beneficios personalizados.
        - Seguimiento completo de referidos y recompensas.
    """,
    'author': 'Wigo',
    'category': 'Sales/CRM',
    'license': 'LGPL-3',
    'icon': '/wigo_planes/static/description/icon.png',
    'depends': ['base', 'mail', 'contacts'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'data': [
        # Seguridad
        'security/ir.model.access.csv',

        # Vistas - Planes
        'views/internet_plan_kanban.xml',
        'views/internet_plan_tree.xml',
        'views/internet_plan_form.xml',
        'views/internet_plan_settings_views.xml',

        # Vistas - Promociones
        'views/promo_views.xml',
        'views/referral_reward_views.xml',

        # Datos
        'data/cron.xml',

        # Menú (siempre al final)
        'views/menu.xml',
    ],
    # CSS registrado aquí (Odoo 17+/19 — NO usar assets.xml en data)
    'assets': {
        'web.assets_backend': [
            'wigo_planes/static/src/css/wigo_planes.css',
        ],
        'web.assets_web_dark': [
            'wigo_planes/static/src/css/wigo_planes.dark.scss',
        ],
    },
}
