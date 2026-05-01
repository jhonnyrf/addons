# -*- coding: utf-8 -*-
{
    'name': 'Diseño Visual Wigo',
    'version': '19.0.1.0',
    'category': 'Customizations',
    'author': 'Wigo',
    'license': 'LGPL-3',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'wigo_visual_design/static/src/scss/navbar_redesign.scss',
            'wigo_visual_design/static/src/js/navbar_improvements.js',
            'wigo_visual_design/static/src/xml/navbar_override.xml',
        ],
    },
    'installable': True,
    'application': False,
}
