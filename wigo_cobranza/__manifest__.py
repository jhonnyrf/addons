# -*- coding: utf-8 -*-
{
    'name': 'Cobranza',
    'version': '19.0.1.0.7',
    'summary': 'Gestión de cobranza, estado de pago y flujo de mora/suspensión — Área Contabilidad',
    'description': """
        Módulo de cobranza para Wigo Fast.
        Cubre:
        - Registro de pagos de clientes
        - Estado de pago visible para todas las áreas
        - Flujo de mora → suspensión → baja con notificaciones
        - Recibos de cobro con previsualización en tiempo real
        - Configuración completa de diseño (colores, fuentes, layout)
        - Vista Kanban elegante para clientes
    """,
    'author': 'Wigo / Asiscore',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'icon': '/wigo_cobranza/static/description/icon.png',
    'depends': ['base', 'mail', 'wigo_ftth', 'wigo_planes', 'customer_contract', 'wigo_crm'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/paperformat_recibo.xml',
        'data/cron.xml',
        'data/sequences.xml',
        'data/cobranza_regla_data.xml',
        'reports/report_recibo_cobro.xml',
        'views/collection_rule_views.xml',
        'views/payment_state_views.xml',
        'views/customer_contract_cobranza_views.xml',
        'views/partner_views.xml',
        'views/receipt_views.xml',
        'views/receipt_config_views.xml',
        'views/adjustment_type_views.xml',
        'views/uncollectible_views.xml',
        'views/invoice_views.xml',
        'views/general_spreadsheet_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wigo_cobranza/static/src/js/semaforo_widget.js',
            'wigo_cobranza/static/src/xml/semaforo_widget.xml',
            'wigo_cobranza/static/src/scss/semaforo_widget.scss',
            # Widget de previsualización en tiempo real del recibo
            'wigo_cobranza/static/src/js/recibo_live_preview.js',
            'wigo_cobranza/static/src/xml/recibo_live_preview.xml',
            # Widget de previsualización reactiva en la configuración del recibo
            'wigo_cobranza/static/src/js/recibo_config_preview.js',
            'wigo_cobranza/static/src/xml/recibo_config_preview.xml',
            # Badge coloreado para tipo de ajuste en listas/form
            'wigo_cobranza/static/src/js/tipo_ajuste_badge.js',
            'wigo_cobranza/static/src/xml/tipo_ajuste_badge.xml',            
        ],
    },
    'external_dependencies': {
        'python': ['num2words'],
    },
}
