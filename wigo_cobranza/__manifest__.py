# -*- coding: utf-8 -*-
{
    'name': 'Wigo Cobranza',
    'version': '19.0.1.0.4',
    'summary': 'Gestión de cobranza, estado de pago y flujo de mora/suspensión — Área Contabilidad',
    'description': """
        Módulo de cobranza para Wigo Fast.
        Cubre:
        - Registro de pagos de clientes (sin reemplazar el sistema SIN/SIAT)
        - Estado de pago visible para todas las áreas (solo lectura para Comercial y Técnica)
        - Flujo de mora → suspensión → baja con notificaciones internas
        - Campo de prorrateo del primer mes (calculado automáticamente)
        - Acciones programadas (cron) para alertas diarias
        - Reportes: mora, suspender hoy, altas/bajas/cambios semanales
    """,
    'author': 'Wigo / Asiscore',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'wigo_ftth', 'wigo_planes', 'customer_contract', 'wigo_crm'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/pago_estado_views.xml',
        'views/pago_estado_contract_workspace_views.xml',
        'views/client_service_cobranza_views.xml',
        'views/customer_contract_cobranza_views.xml',
        'views/res_partner_cobranza_views.xml',
        'views/reporte_mora_views.xml',
        'views/menu.xml',
    ],
}
