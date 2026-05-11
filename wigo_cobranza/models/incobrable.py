# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WigoIncobrable(models.Model):
    """
    Registro de deudas declaradas incobrables por Contabilidad.
    Un cliente puede tener varios registros (uno por período adeudado).
    """
    _name = 'wigo.incobrable'
    _description = 'Deuda Incobrable'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_declaracion desc'
    _rec_name = 'display_name'

    # ── Identificación ───────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict', tracking=True, index=True,
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
        tracking=True,
    )
    contract_phone = fields.Char(
        string='Teléfono del contrato',
        related='contract_id.phone', store=True, readonly=True,
    )
    contract_mobile = fields.Char(
        string='Móvil del contrato',
        related='contract_id.mobile', store=True, readonly=True,    
    )
    contract_date = fields.Date(
        string='Fecha del contrato',
        related='contract_id.contract_date', store=True, readonly=True,
    )
    
    client_service_id = fields.Many2one(
        'wigo.ftth.client.service', string='Servicio (CF)',
        ondelete='restrict', tracking=True,
    )
    suspension_id = fields.Many2one(
        'wigo.ftth.service.suspension',
        string='Suspensión FTTH',
        ondelete='set null',
        tracking=True,
    )
    codigo_cliente = fields.Char(
        string='Código CF',
        compute='_compute_datos_cliente', store=True,
    )
    plan_id = fields.Many2one(
        'internet.plan', string='Plan',
        compute='_compute_datos_cliente', store=True,
    )
    monto_plan = fields.Float(
        string='Monto del plan (Bs)',
        related='plan_id.price', store=True, readonly=True,
    )
    plan_identifier = fields.Char(
        string='Identificador del plan',
        related='plan_id.plan_identifier', store=True, readonly=True,
    )

    # ── Deuda ────────────────────────────────────────────────────
    meses_adeudados = fields.Char(
        string='Meses adeudados',
        help='Ej: Enero, Febrero/2026',
        tracking=True,
    )
    monto_total_adeudado = fields.Float(
        string='Monto total adeudado (Bs)',
        tracking=True,
    )    
    monto_cobrado = fields.Float(
        string='Monto cobrado efectivamente (Bs)',
        tracking=True,
    )
    diferencia_incobrable = fields.Float(
        string='Monto incobrable definitivo (Bs)',
        compute='_compute_diferencia_incobrable', store=True,
    )

    # ── Estado y fechas ──────────────────────────────────────────
    fecha_declaracion = fields.Date(
        string='Fecha de declaración',
        default=lambda self: fields.Date.context_today(self),
        required=True, tracking=True,
    )
    fecha_baja_servicio = fields.Date(
        string='Fecha baja de servicio', tracking=True,
    )
      
    state = fields.Selection([
        ('activo', 'En gestión'),   
        ('in_cut', 'En corte'),
        ('baja_incobrable', 'Baja - Incobrable'),
        ('recuperado', 'Recuperado')        
    ], string='Estado', default='activo', required=True, tracking=True, index=True)

    # ── Observaciones ────────────────────────────────────────────
    observaciones = fields.Text(string='Observaciones')

    # ── Display ──────────────────────────────────────────────────
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('partner_id', 'contract_id', 'client_service_id')
    def _compute_datos_cliente(self):
        for rec in self:
            rec.codigo_cliente = (
                rec.contract_id.name or
                rec.client_service_id.codigo_cliente or
                False
            )
            rec.plan_id = (
                rec.contract_id.plan_id or
                rec.client_service_id.plan_id or
                False
            )

    @api.depends('monto_total_adeudado', 'monto_cobrado')
    def _compute_diferencia_incobrable(self):
        for rec in self:
            rec.diferencia_incobrable = (
                rec.monto_total_adeudado -                
                rec.monto_cobrado
            )

    @api.depends('partner_id', 'meses_adeudados')
    def _compute_display_name(self):
        for rec in self:
            nombre = rec.partner_id.name or ''
            rec.display_name = f"{nombre} — {rec.meses_adeudados}" if rec.meses_adeudados else nombre

    def action_marcar_baja_incobrable(self):
        for rec in self:
            rec.state = 'baja_incobrable'
            if not rec.fecha_baja_servicio:
                rec.fecha_baja_servicio = date.today()
            # Marcar el servicio como baja si existe
            if rec.client_service_id:
                rec.client_service_id.estado_pago = 'baja_definitiva'
                if rec.client_service_id.estado_servicio != 'baja':
                    rec.client_service_id.estado_servicio = 'baja'
                    rec.client_service_id.fecha_baja = date.today()

    def _get_periodos_adeudados_list(self):
        self.ensure_one()
        if not self.meses_adeudados:
            return []
        return [p.strip() for p in self.meses_adeudados.split(',') if p.strip()]

    def action_marcar_en_corte(self):
        for rec in self:
            if rec.state in ('recuperado', 'baja_incobrable'):
                raise ValidationError(
                    'No se puede cambiar a "En corte" un registro recuperado o con baja incobrable.'
                )
            rec.state = 'in_cut'
            suspension = rec._get_or_create_suspension_record()
            if suspension:
                rec.suspension_id = suspension.id

    def _get_or_create_suspension_record(self):
        self.ensure_one()
        Suspension = self.env['wigo.ftth.service.suspension'].sudo()
        domain = [('contract_id', '=', self.contract_id.id)]
        if self.client_service_id:
            domain.append(('client_service_id', '=', self.client_service_id.id))

        suspension = Suspension.search(
            domain + [('state', 'in', ('pendiente', 'in_cut'))],
            order='fecha_registro desc, id desc',
            limit=1,
        )
        if suspension:
            if suspension.state == 'pendiente':
                suspension.action_marcar_en_corte()
            elif suspension.state == 'in_cut' and not suspension.fecha_corte:
                suspension._ensure_cut_date()
            return suspension

        vals = {
            'contract_id': self.contract_id.id,
            'client_service_id': self.client_service_id.id if self.client_service_id else False,
            'state': 'pendiente',
            'fecha_corte': date.today(),
        }
        return Suspension.create(vals)

    def action_view_suspension(self):
        self.ensure_one()
        if not self.suspension_id:
            raise ValidationError('Este registro incobrable todavía no tiene una suspensión asociada.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Suspensión FTTH',
            'res_model': 'wigo.ftth.service.suspension',
            'view_mode': 'form',
            'res_id': self.suspension_id.id,
            'target': 'current',
        }

    def action_marcar_recuperado(self):
        for rec in self:
            """if rec.state == 'baja_incobrable':
                raise ValidationError(
                    'No se puede marcar como recuperado un registro con estado "Baja - Incobrable".'
            ) """

            if not rec.contract_id:
                raise ValidationError(
                    'No se puede validar recuperación sin contrato asociado.'
                )

            periodos_adeudados = rec._get_periodos_adeudados_list()
            if not periodos_adeudados:
                raise ValidationError(
                    'No se pudieron identificar los meses adeudados para validar recuperación.'
                )

            pago_pagado = self.env['wigo.pago.estado'].sudo().search([
                ('contract_id', '=', rec.contract_id.id),
                ('estado_pago', '=', 'pagado'),
                ('periodo', 'in', periodos_adeudados),
            ], limit=1)

            if not pago_pagado:
                raise ValidationError(
                    'Para marcar como recuperado debe existir al menos 1 mes pagado '
                    f'de los adeudados: {", ".join(periodos_adeudados)}.'
                )

            rec.state = 'recuperado'

    def action_open_pagos_contrato(self):
        """Abre la lista de `wigo.pago.estado` filtrada por el contrato asociado.

        Visible en formulario de incobrable cuando existe `contract_id`.
        """
        self.ensure_one()
        if not self.contract_id:
            raise ValidationError('No hay contrato asociado a este registro incobrable.')

        action = {
            'type': 'ir.actions.act_window',
            'name': f'Pagos — {self.contract_id.name or self.partner_id.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.contract_id.id)],
            'context': {'default_contract_id': self.contract_id.id},
            'target': 'current',
        }

        # Priorizar las vistas específicas del workspace de contrato si existen
        list_view = self.env.ref('wigo_cobranza.view_payment_state_list', raise_if_not_found=False)
        form_view = self.env.ref('wigo_cobranza.view_payment_state_form', raise_if_not_found=False)
        views = []
        if list_view:
            # en algunos módulos se declara como tipo 'list' (workspace), respetarlo
            views.append((list_view.id, list_view.type or 'list'))
        if form_view:
            views.append((form_view.id, form_view.type or 'form'))

        if views:
            action['views'] = views
            # forzar view_mode coherente
            action['view_mode'] = ','.join([t for _, t in views])
            return action

        # Fallback: buscar vistas tree/form registradas para el modelo
        View = self.env['ir.ui.view'].sudo()
        found_views = View.search([
            ('model', '=', 'wigo.pago.estado'),
            ('type', 'in', ('tree', 'form')),
        ])
        ordered = []
        tree_views = [v for v in found_views if v.type == 'tree']
        form_views = [v for v in found_views if v.type == 'form']
        for v in tree_views + form_views:
            ordered.append((v.id, v.type))
        if ordered:
            # preferir la vista tree (lista)
            for vid, vtype in ordered:
                if vtype == 'tree':
                    action['views'] = [(vid, 'tree')]
                    action['view_mode'] = 'tree'
                    return action
            action['views'] = ordered

        return action

    @api.model
    def crear_desde_pago_mora(self, pago_estado):
        """
        Crea un registro incobrable a partir de un pago en mora.
        Llamado desde la acción de baja definitiva del pago.
        """
        existing = self.search([
            ('partner_id', '=', pago_estado.partner_id.id),
            ('contract_id', '=', pago_estado.contract_id.id),
            ('state', '!=', 'recuperado'),
        ], limit=1)
        if existing:
            return existing

        return self.create({
            'partner_id': pago_estado.partner_id.id,
            'contract_id': pago_estado.contract_id.id,
            'client_service_id': pago_estado.client_service_id.id or False,
            'meses_adeudados': pago_estado.periodo,
            'monto_total_adeudado': pago_estado.monto_a_cobrar,
            'state': 'activo',
        })
