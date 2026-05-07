# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WigoCobranzaRegla(models.Model):
    """
    Configuración de reglas de cobranza.
    Define de forma data-driven:
    - Día de generación automática del debe
    - Días para entrar en mora
    - Días para pasar a incobrable
    - Aplica por modalidad de pago (prepaid/postpaid/all)
    """
    _name = 'wigo.cobranza.regla'
    _description = 'Regla de Cobranza'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nombre de la regla',
        required=True,
    )
    active = fields.Boolean(
        string='Activa',
        default=True,
    )
    sequence = fields.Integer(
        string='Prioridad',
        default=10,
        help='Orden de evaluación. Menor = mayor prioridad.',
    )
    payment_mode = fields.Selection([
        ('all', 'Todas las modalidades'),
        ('prepaid', 'Prepago'),
        ('postpaid', 'Postpago'),
    ],
        string='Modalidad de pago',
        required=True,
        default='all',
        help='A qué modalidad aplica esta regla. "Todas" aplica a cualquiera.',
    )
    dia_generacion = fields.Integer(
        string='Día de generación (1-28)',
        required=True,
        default=1,
        help='Día del mes en que se genera automáticamente el debe.',
    )
    generacion_automatica = fields.Boolean(
        string='Generación automática activada',
        default=True,
    )
    mora_criterio = fields.Selection([
        ('dias', 'Días'),
        ('meses', 'Meses'),
    ],
        string='Criterio de Mora',
        required=True,
        default='meses',
        help='Si se configura por días o por meses.',
    )
    dias_mora = fields.Integer(
        string='Días para Mora',
        required=True,
        default=30,
        help='Días de atraso desde la fecha de vencimiento para pasar a estado Mora.',
    )
    meses_mora = fields.Integer(
        string='Meses para Mora',
        default=1,
        help='Meses de atraso desde la fecha de vencimiento para pasar a estado Mora.',
    )
    incobrable_criterio = fields.Selection([
        ('dias', 'Días'),
        ('meses', 'Meses'),
    ],
        string='Criterio de Incobrable',
        required=True,
        default='meses',
        help='Si se configura por días o por meses.',
    )
    dias_incobrable = fields.Integer(
        string='Días para Incobrable',
        required=True,
        default=90,
        help='Días de atraso desde la fecha de vencimiento para pasar a Incobrable.',
    )
    meses_incobrable = fields.Integer(
        string='Meses consecutivos para Incobrable',
        default=3,
        help='Cantidad de meses consecutivos sin pago para crear registro incobrable.',
    )
    estado_inicial = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    ],
        string='Estado inicial del debe',
        required=True,
        default='pendiente',
    )

    @api.constrains('dia_generacion')
    def _check_dia_generacion(self):
        for rec in self:
            if not (1 <= rec.dia_generacion <= 28):
                raise ValidationError(
                    'El día de generación debe estar entre 1 y 28.'
                )

    @api.constrains('dias_mora', 'dias_incobrable', 'meses_mora', 'meses_incobrable')
    def _check_dias(self):
        for rec in self:
            if rec.mora_criterio == 'dias' and rec.dias_mora < 0:
                raise ValidationError('Los días para mora no pueden ser negativos.')
            if rec.mora_criterio == 'meses' and rec.meses_mora < 0:
                raise ValidationError('Los meses para mora no pueden ser negativos.')
            if rec.incobrable_criterio == 'dias' and rec.dias_incobrable < 0:
                raise ValidationError('Los días para incobrable no pueden ser negativos.')
            if rec.incobrable_criterio == 'meses' and rec.meses_incobrable < 0:
                raise ValidationError('Los meses para incobrable no pueden ser negativos.')
            if rec.incobrable_criterio == 'dias' and rec.mora_criterio == 'dias' and rec.dias_incobrable <= rec.dias_mora:
                raise ValidationError(
                    'Los días para incobrable deben ser mayores que los días para mora.'
                )

    def _get_rule_for_contract(self, contract):
        """
        Devuelve la regla aplicable para un contrato.
        Si el contrato tiene payment_mode 'prepaid' o 'postpaid', busca regla con ese
        valor o 'all'. Se ordena por sequence para priorizar reglas más específicas.
        """
        if not contract:
            return self.env['wigo.cobranza.regla']
        domain = [
            ('active', '=', True),
            ('payment_mode', 'in', [contract.payment_mode, 'all']),
        ]
        return self.search(domain, order='sequence, id', limit=1)

    @api.model
    def _get_generation_rules_for_day(self, day=None):
        """Reglas activas que deben dispararse en un día específico."""
        day = day if day is not None else fields.Date.context_today(self).day
        return self.search([
            ('active', '=', True),
            ('generacion_automatica', '=', True),
            ('dia_generacion', '=', day),
        ], order='sequence, id')
