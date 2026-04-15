# -*- coding: utf-8 -*-
{
    'name': 'Contactos Ext',
    'summary': 'Personalización del módulo de contactos para Wigo',
    'description': """
        Extiende res.partner con:
        - CI / Celular (principal) + Teléfono fijo
        - Planes contratados (One2many con código CF-XXX, estado, fechas)
        - Referidos: lista de clientes recomendados (fuente: wigo.promo.referral)
        - Sección informativa si el contacto fue recomendado por otro
        - Empleado flag
        - Filtros y búsquedas personalizadas
    """,
    'author': 'Wigo',
    'category': 'Contacts',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts', 'crm', 'wigo_planes', 'wigo_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}
