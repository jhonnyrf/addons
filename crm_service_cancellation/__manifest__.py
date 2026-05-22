# -*- coding: utf-8 -*-
{
    'name': 'CRM - Baja de Servicio',
    'version': '19.0.3.0.0',
    'summary': 'Gestión de bajas de servicio desde el CRM',
    'description': """
        Módulo técnico que extiende el CRM de Wigo para registrar bajas de clientes.
        - Botón "Dar de baja" en leads ganados
        - Wizard con datos del cliente autorellenados (CI, código, contrato)
        - Catálogo editable de motivos de baja dentro de CRM > Configuración
        - Datos del ONU
        - Registro histórico de bajas (service.cancellation)
        - Terminación automática del contrato vinculado
        - Menú de bajas dentro de CRM
    """,
    'author': 'Wigo',
    'category': 'Sales',
    'license': 'LGPL-3',
    'depends': ['crm', 'wigo_crm', 'customer_contract', 'wigo_ftth', 'wigo_cobranza'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/cancellation_reason_views.xml',
        'views/service_cancellation_views.xml',
        'views/cancellation_wizard_views.xml',
        'views/crm_lead_cancellation_views.xml',
        'views/crm_menu_cancellation_views.xml',
        'views/mail_activity_post_sale_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
