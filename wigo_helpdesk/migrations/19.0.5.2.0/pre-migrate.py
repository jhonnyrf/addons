# -*- coding: utf-8 -*-
def migrate(cr, version):
    # Agregar columna area_id si no existe
    cr.execute("""
        ALTER TABLE helpdesk_knowledge
        ADD COLUMN IF NOT EXISTS area_id INTEGER
    """)
    # Eliminar columna area si existe (era selection)
    cr.execute("""
        ALTER TABLE helpdesk_knowledge
        DROP COLUMN IF EXISTS area
    """)
    # Agregar columna ticket_type_id si no existe
    cr.execute("""
        ALTER TABLE helpdesk_knowledge
        ADD COLUMN IF NOT EXISTS ticket_type_id INTEGER
    """)
    # Eliminar columna category_id si existe
    cr.execute("""
        ALTER TABLE helpdesk_knowledge
        DROP COLUMN IF EXISTS category_id
    """)
    # Eliminar columna views si existe
    cr.execute("""
        ALTER TABLE helpdesk_knowledge
        DROP COLUMN IF EXISTS views
    """)
    # Eliminar columna tag_ids si existe (era many2many)
    cr.execute("""
        DROP TABLE IF EXISTS helpdesk_knowledge_tag_rel
    """)