# -*- coding: utf-8 -*-
{
    'name': 'Helpdesk WigoFast',
    'version': '19.0.5.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Gestión de tickets de soporte para ISP WigoFast',
    'description': """
        Módulo Helpdesk WigoFast (Odoo 19) — v5
        =========================================
        - Kanban simplificado: Nuevo / En Proceso / En Espera / Resuelto / Concluido
        - Tipo de Ticket: Reclamo/Incidente vs Solicitud (reemplaza Categoría)
        - Diagnóstico y Solución movidos a pestaña Resolución
        - Visita Técnica: solo asignación y programación (sin diagnóstico)
        - Tipos no-técnicos archivados (instalación, baja, cambio domicilio → Órdenes de Trabajo)
        - Pestaña Tickets en formulario de Contacto (res.partner)
        - Clientes Recurrentes: lista y acceso rápido desde menú
        - Gráficas: por Diagnóstico, Solución, Mes, Top Clientes, Etapas
        - Búsqueda mejorada: filtros por tipo, diagnóstico, solución, mes
        - Semáforo SLA dinámico y configurable: verde/amarillo/rojo
        - SLA por prioridad (Crítica/Alta/Media/Baja) editable
        - Auto-llenado de campos al asociar cliente (res.partner)
        - Cron automático: mueve ticket a En Espera al vencer SLA
        - Escalamiento entre técnica y comercial
        - Seguimiento postventa con nivel de satisfacción
        - Reportes PDF
        - Base de conocimiento
    """,
    'author': 'WigoFast',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'hr', 'customer_contract', 'wigo_ftth'],
    'post_init_hook': 'post_init_hook',
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk_stage_data.xml',
        'data/helpdesk_incident_type_data.xml',
        'data/helpdesk_category_data.xml',
        'data/helpdesk_visit_type_data.xml',
        'data/helpdesk_sequence_data.xml',
        'data/helpdesk_cron_data.xml',
        'data/helpdesk_sla_config_data.xml',
        'views/helpdesk_incident_type_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_ticket_search_view.xml',
        'views/helpdesk_stage_views.xml',
        'views/helpdesk_category_views.xml',
        'views/helpdesk_visit_type_views.xml',
        'views/helpdesk_team_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_knowledge_views.xml',
        'views/helpdesk_sla_config_views.xml',
        'views/res_partner_views.xml',
        'views/helpdesk_menu.xml',
        'report/helpdesk_ticket_report.xml',
        'report/helpdesk_ticket_report_template.xml',
        'wizard/assign_ticket_wizard_views.xml',
        'wizard/close_ticket_wizard_views.xml',
        'wizard/sla_advanced_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wigo_helpdesk/static/src/css/helpdesk_ticket_form.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
