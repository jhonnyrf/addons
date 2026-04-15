# -*- coding: utf-8 -*-
from . import models
from . import wizard
from .migrations.migrate_zona_to_zona_id import post_init_migrate_zona_to_zona_id

__all__ = ['post_init_migrate_zona_to_zona_id']
