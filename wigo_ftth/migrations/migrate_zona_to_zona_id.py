# -*- coding: utf-8 -*-
"""
Migración: Convertir campo zona (Char) a zona_id (Many2one)

Este script migra los datos del campo zona (Char) en wigo.ftth.box.group
a referencias Many2one al modelo wigo.zone, asegurando que:

1. Se creen registros en wigo.zone por cada valor único de zona
2. Se actualicen los registros de box_group con la relación correcta
3. Se mantengan todos los datos sin pérdida
4. Se evite duplicados

Uso:
    El script se ejecuta automáticamente durante la actualización del módulo
    gracias a la entrada en __manifest__.py:
    
    'post_init_hook': 'post_init_migrate_zona_to_zona_id'

Ejecución manual (si es necesario):
    from odoo import api
    from odoo.modules.registry import Registry
    
    env = api.Environment(cr, uid, {})
    env['wigo.ftth.box.group']._migrate_zona_to_zona_id()
"""

def post_init_migrate_zona_to_zona_id(cr, registry):
    """
    Hook post-instalación para migrar datos de zona a zona_id.
    Se ejecuta automáticamente después de instalar/actualizar el módulo.
    """
    from odoo.api import Environment
    
    # Obtener el cursor y crear un environment
    env = Environment(cr, registry.db_name, registry.uid, {})
    
    # Realizar la migración
    env['wigo.ftth.box.group']._migrate_zona_to_zona_id()


def migrate_zona_to_zona_id(cr, uid, registry):
    """
    Función alternativa de migración (uso en pre_init_hook si es necesario).
    """
    from odoo.api import Environment
    
    env = Environment(cr, registry.db_name, registry.uid, {})
    env['wigo.ftth.box.group']._migrate_zona_to_zona_id()
