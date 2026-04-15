# -*- coding: utf-8 -*-
{
    'name': 'Wigo FTTH',
    'version': '19.0.2.0.0',
    'summary': 'Gestion de red GPON/FTTH — Topologia, ONUs, Ordenes de Trabajo, Ficha Tecnica y Reportes',
    'description': """
        Modulo central del Area Tecnica de Wigo Fast.
        Reemplaza el Excel BD_FTTH con gestion estructurada de:
        - Topologia de red: Regional > Nodo > OLT > Puerto > ODN (ODF) > Grupo (Splitters) > NAP > Puerto > Subinterfaz
        - Inventario de equipos ONU/ONT con lotes de entrega y accesorios
        - Tecnicos e instaladores externos
        - Ordenes de Trabajo (instalacion y baja) con flujo de estados
        - Ficha tecnica unificada del cliente con equipos adicionales y control de acceso por rol
        - Vista de ocupacion de puertos OLT
        - Reportes y graficas: por estado, plan, mes, instalador, nodo
    """,
    'author': 'Wigo',
    'category': 'Technical',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'contacts', 'crm', 'wigo_crm', 'wigo_planes','hr'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv', 
        'data/sequence.xml',      
        'views/topology_views.xml',
        'views/generate_ports_wizard.xml',
        'views/generic_confirm_wizard.xml',
        'views/onu_views.xml',
        'views/installer_views.xml',
        'views/work_order_views.xml',
        'views/client_service_views.xml',
        'views/capacity_views.xml',
        'views/dashboard_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wigo_ftth/static/src/css/wigo_ftth.css',
        ],
    },
    'post_init_hook': 'post_init_migrate_zona_to_zona_id',
}
