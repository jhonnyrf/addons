# -*- coding: utf-8 -*-
import calendar
import base64
from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class WigoPagoEstado(models.Model):
    """
    Registro de pago mensual por cliente.
    Reemplaza el Excel de Dania sin tocar el sistema contable SIN/SIAT.
    Una fila = un mes de un cliente.
    """
    _name = 'wigo.pago.estado'
    _description = 'Registro de Pago Mensual del Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anio desc, mes desc, partner_id'
    _rec_name = 'display_name'

    # ── Identificación ────────────────────────────────────────────
    eligible_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_eligible_partner_ids',
        string='Clientes con contrato activo',
        store=False,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict', tracking=True, index=True,
        domain="[('id', 'in', eligible_partner_ids)]",
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
        domain="[('partner_id', '=', partner_id), ('state', '=', 'active')]",
        tracking=True,
        required=True,
    )
    client_service_id = fields.Many2one(
        'wigo.ftth.client.service', string='Servicio (CF)',
        domain="[('partner_id', '=', partner_id)]",
        ondelete='restrict', tracking=True, index=True,
    )
    codigo_cliente = fields.Char(string='Código CF', compute='_compute_contract_service_data', store=True, readonly=True)
    plan_id = fields.Many2one('internet.plan', string='Plan', compute='_compute_contract_service_data', store=True, readonly=True)
    partner_ci = fields.Char(string='CI', compute='_compute_partner_snapshot', store=False)
    partner_celular = fields.Char(string='Celular', compute='_compute_partner_snapshot', store=False)
    partner_telefono = fields.Char(string='Teléfono', compute='_compute_partner_snapshot', store=False)
    partner_email = fields.Char(string='Correo', compute='_compute_partner_snapshot', store=False)
    partner_direccion = fields.Char(string='Dirección', compute='_compute_partner_snapshot', store=False)
    contract_state = fields.Selection(
        related='contract_id.state',
        string='Estado de contrato',
        readonly=True,
        store=False,
    )
    crm_lead_id = fields.Many2one(
        'crm.lead', string='Lead CRM',
        compute='_compute_crm_data', store=False, readonly=True,
    )
    crm_zona = fields.Char(string='Zona CRM', compute='_compute_crm_data', store=False)
    crm_direccion = fields.Char(string='Dirección CRM', compute='_compute_crm_data', store=False)
    crm_ubicacion = fields.Char(string='Ubicación CRM', compute='_compute_crm_data', store=False)
    crm_coordenadas = fields.Char(string='Coordenadas CRM', compute='_compute_crm_data', store=False)

    # ── Período ───────────────────────────────────────────────────
    anio = fields.Integer(
        string='Año', required=True,
    )
    mes = fields.Selection(
        [(str(i), name) for i, name in enumerate([
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
        ], start=0) if i > 0],
        string='Mes', required=True,
    )
    periodo = fields.Char(
        string='Período', compute='_compute_periodo', store=True,
    )

    # ── Montos ────────────────────────────────────────────────────
    monto_plan = fields.Float(
        string='Monto del plan (Bs)',
        related='plan_id.price', store=True, readonly=True,
    )
    monto_prorrateo = fields.Float(
        string='Monto prorrateo (Bs)',
        compute='_compute_prorrateo', store=True,
        help='Calculado solo para el primer mes según fecha de instalación.',
    )
    es_primer_mes = fields.Boolean(
        string='¿Es primer mes?',
        compute='_compute_prorrateo', store=True,
    )
    monto_a_cobrar = fields.Float(
        string='Monto a cobrar (Bs)',
        compute='_compute_monto_a_cobrar', store=True,
        help='Prorrateo si es primer mes, tarifa completa en el resto.',
    )
    monto_pagado = fields.Float(
        string='Monto pagado (Bs)', tracking=True,
    )
    diferencia = fields.Float(
        string='Diferencia (Bs)',
        compute='_compute_diferencia', store=True,
    )

    # ── Pago ──────────────────────────────────────────────────────
    fecha_pago = fields.Date(
        string='Fecha de pago',
        tracking=True,
        default=lambda self: fields.Date.context_today(self),
    )
    canal_pago = fields.Selection([
        ('qr',           'QR bancario'),
        ('transferencia','Transferencia bancaria'),
        ('efectivo',     'Efectivo en oficina'),
    ], string='Canal de pago', tracking=True)
    comprobante = fields.Char(string='Referencia / N° comprobante', tracking=True)
    comprobante_adjunto = fields.Binary(string='Comprobante (imagen o PDF)')
    comprobante_adjunto_fname = fields.Char()
    comprobante_adjunto_is_image = fields.Boolean(
        string='Adjunto es imagen', compute='_compute_comprobante_adjunto_type', store=False,
    )
    comprobante_adjunto_is_pdf = fields.Boolean(
        string='Adjunto es PDF', compute='_compute_comprobante_adjunto_type', store=False,
    )
    registrado_por = fields.Many2one(
        'res.users', string='Registrado por',
        default=lambda self: self.env.user, tracking=True,
    )

    # ── Estado ────────────────────────────────────────────────────
    estado_pago = fields.Selection([
        ('al_dia',         'Al día'),
        ('pendiente',      'Pendiente'),
        ('mora',           'En mora'),
        ('deuda_parcial',  'Deuda parcial'),
        ('baja_definitiva','Baja definitiva'),
    ], string='Estado de pago', default='pendiente',
       required=True, tracking=True, index=True,
    )

    # ── Notas ─────────────────────────────────────────────────────
    notas = fields.Text(string='Notas de cobranza')

    # ── Display ───────────────────────────────────────────────────
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ─────────────────────────────────────────────────────────────
    # Constraints (Odoo 19: @api.constrains en lugar de _sql_constraints)
    # ─────────────────────────────────────────────────────────────
    @api.constrains('contract_id', 'client_service_id', 'mes', 'anio')
    def _check_unique_cliente_periodo(self):
        for rec in self:
            if not rec.contract_id and not rec.client_service_id:
                continue
            domain = [
                ('mes', '=', rec.mes),
                ('anio', '=', rec.anio),
                ('id', '!=', rec.id),
            ]
            if rec.contract_id:
                domain.append(('contract_id', '=', rec.contract_id.id))
            else:
                domain.append(('client_service_id', '=', rec.client_service_id.id))
            duplicado = self.search(domain, limit=1)
            if duplicado:
                periodo_txt = rec.periodo or (
                    f"{dict(self._fields['mes'].selection).get(rec.mes, '')} {rec.anio}".strip()
                    if rec.mes and rec.anio else ''
                )
                raise ValidationError(
                    f'Ya existe un registro de pago para {rec.codigo_cliente} '
                    f'en el periodo {periodo_txt}.'
                )

    @api.constrains('partner_id')
    def _check_partner_has_contract(self):
        Contract = self.env['customer.contract']
        for rec in self:
            if not rec.partner_id:
                continue
            has_contract = Contract.search_count([
                ('partner_id', '=', rec.partner_id.id),
                ('state', '=', 'active'),
            ])
            if not has_contract:
                raise ValidationError(
                    f"El cliente '{rec.partner_id.name}' no tiene contrato activo."
                )

    # ─────────────────────────────────────────────────────────────
    # Computes
    # ─────────────────────────────────────────────────────────────
    @api.depends('anio', 'mes')
    def _compute_periodo(self):
        for rec in self:
            if rec.mes and rec.anio:
                month_name = dict(self._fields['mes'].selection).get(rec.mes, '')
                rec.periodo = f"{month_name} {rec.anio}".strip()
            else:
                rec.periodo = ''

    def _suggest_next_period_values(self, contract=None, client_service=None, partner=None):
        domain = []
        if contract:
            domain.append(('contract_id', '=', contract.id))
        elif client_service:
            domain.append(('client_service_id', '=', client_service.id))
        elif partner:
            domain.append(('partner_id', '=', partner.id))

        if not domain:
            return str(date.today().month), date.today().year

        records = self.search(domain)
        if not records:
            return str(date.today().month), date.today().year

        last_record = max(
            records,
            key=lambda rec: (int(rec.anio or 0), int(rec.mes or 0), rec.id or 0),
        )
        mes_actual = int(last_record.mes or date.today().month)
        anio_actual = int(last_record.anio or date.today().year)
        if mes_actual >= 12:
            return '1', anio_actual + 1
        return str(mes_actual + 1), anio_actual

    def _apply_next_period_for_new_record(self):
        for rec in self:
            if rec.id:
                continue
            mes_sugerido, anio_sugerido = rec._suggest_next_period_values(
                contract=rec.contract_id,
                client_service=rec.client_service_id,
                partner=rec.partner_id,
            )
            rec.mes = mes_sugerido
            rec.anio = anio_sugerido

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        contract_id = res.get('contract_id') or self.env.context.get('default_contract_id')
        service_id = res.get('client_service_id') or self.env.context.get('default_client_service_id')
        partner_id = res.get('partner_id') or self.env.context.get('default_partner_id')

        if not contract_id and partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            contract = self._get_preferred_contract(partner)
            if contract:
                contract_id = contract.id
                if 'contract_id' in fields_list:
                    res['contract_id'] = contract.id

        if (not service_id) and contract_id:
            contract = self.env['customer.contract'].browse(contract_id)
            service = self._find_client_service_for_contract(contract)
            if service:
                service_id = service.id
                if 'client_service_id' in fields_list:
                    res['client_service_id'] = service.id

        if ('mes' in fields_list and not res.get('mes')) or ('anio' in fields_list and not res.get('anio')):
            mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                contract=self.env['customer.contract'].browse(contract_id) if contract_id else None,
                client_service=self.env['wigo.ftth.client.service'].browse(service_id) if service_id else None,
                partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
            )
            if 'mes' in fields_list and not res.get('mes'):
                res['mes'] = mes_sugerido
            if 'anio' in fields_list and not res.get('anio'):
                res['anio'] = anio_sugerido

        return res

    def _sync_payment_defaults(self):
        for rec in self:
            if rec.monto_a_cobrar and not rec.monto_pagado:
                rec.monto_pagado = rec.monto_a_cobrar

    def _compute_eligible_partner_ids(self):
        Contract = self.env['customer.contract']
        partner_ids = Contract.search([
            ('state', '=', 'active'),
        ]).mapped('partner_id').ids
        for rec in self:
            rec.eligible_partner_ids = [(6, 0, partner_ids)]

    @api.depends('contract_id.name', 'contract_id.plan_id', 'client_service_id.codigo_cliente', 'client_service_id.plan_id')
    def _compute_contract_service_data(self):
        for rec in self:
            rec.codigo_cliente = rec.contract_id.name or rec.client_service_id.codigo_cliente or False
            rec.plan_id = rec.contract_id.plan_id or rec.client_service_id.plan_id or False

    @api.depends('partner_id')
    def _compute_partner_snapshot(self):
        for rec in self:
            partner = rec.partner_id
            rec.partner_ci = (getattr(partner, 'ci', False) or False) if partner else False
            rec.partner_celular = (
                getattr(partner, 'celular', False) or
                getattr(partner, 'mobile', False) or
                getattr(partner, 'phone', False) or
                False
            ) if partner else False
            rec.partner_telefono = getattr(partner, 'phone', False) if partner else False
            rec.partner_email = partner.email if partner else False
            rec.partner_direccion = (
                getattr(partner, 'direccion', False) or partner.street or False
            ) if partner else False

    @api.depends('client_service_id', 'contract_id', 'mes', 'anio', 'monto_plan')
    def _compute_prorrateo(self):
        for rec in self:
            svc = rec.client_service_id
            contract = rec.contract_id
            fecha_instalacion = svc.fecha_instalacion if svc else (contract.installation_date if contract else False)
            if not fecha_instalacion or not rec.mes or not rec.anio:
                rec.es_primer_mes = False
                rec.monto_prorrateo = 0.0
                continue

            fi = fecha_instalacion
            mes_int = int(rec.mes)
            anio_int = int(rec.anio)

            if fi.month == mes_int and fi.year == anio_int:
                # Es el primer mes: calcular prorrateo
                dias_mes = calendar.monthrange(anio_int, mes_int)[1]
                dias_restantes = dias_mes - fi.day + 1
                precio = rec.monto_plan or (svc.plan_id.price if (svc and svc.plan_id) else (contract.plan_id.price if (contract and contract.plan_id) else 0.0))
                rec.es_primer_mes = True
                rec.monto_prorrateo = round((precio / dias_mes) * dias_restantes, 2)
            else:
                rec.es_primer_mes = False
                rec.monto_prorrateo = 0.0

    @api.depends('es_primer_mes', 'monto_prorrateo', 'monto_plan')
    def _compute_monto_a_cobrar(self):
        for rec in self:
            if rec.es_primer_mes:
                rec.monto_a_cobrar = rec.monto_prorrateo
            else:
                rec.monto_a_cobrar = rec.monto_plan

    @api.depends('monto_a_cobrar', 'monto_pagado')
    def _compute_diferencia(self):
        for rec in self:
            rec.diferencia = rec.monto_pagado - rec.monto_a_cobrar

    @api.depends('comprobante_adjunto', 'comprobante_adjunto_fname')
    def _compute_comprobante_adjunto_type(self):
        for rec in self:
            name = (rec.comprobante_adjunto_fname or '').lower()
            is_image = bool(name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')))
            is_pdf = name.endswith('.pdf')

            # Fallback when filename is missing: detect by file signature in base64 payload.
            if rec.comprobante_adjunto and not (is_image or is_pdf):
                try:
                    raw = base64.b64decode(rec.comprobante_adjunto)
                    if raw.startswith(b'%PDF'):
                        is_pdf = True
                    elif (
                        raw.startswith(b'\xff\xd8\xff') or
                        raw.startswith(b'\x89PNG\r\n\x1a\n') or
                        raw.startswith(b'GIF87a') or
                        raw.startswith(b'GIF89a') or
                        raw.startswith(b'RIFF')
                    ):
                        is_image = True
                except Exception:
                    # Keep both flags false if payload cannot be decoded.
                    pass

            rec.comprobante_adjunto_is_image = is_image
            rec.comprobante_adjunto_is_pdf = is_pdf

    @api.depends('partner_id', 'periodo')
    def _compute_display_name(self):
        for rec in self:
            nombre = rec.partner_id.name or ''
            rec.display_name = f"{nombre} — {rec.periodo}" if rec.periodo else nombre

    @api.depends('client_service_id.lead_id', 'contract_id.lead_id')
    def _compute_crm_data(self):
        for rec in self:
            lead = rec.client_service_id.lead_id or rec.contract_id.lead_id
            rec.crm_lead_id = lead
            rec.crm_zona = lead.zona if lead else False
            rec.crm_direccion = lead.direccion if lead else False
            rec.crm_ubicacion = lead.ubicacion if lead else False
            rec.crm_coordenadas = lead.coordenadas if lead else False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id:
            self.contract_id = False
            self.client_service_id = False
            return

        if not self.contract_id or self.contract_id.partner_id != self.partner_id:
            self.contract_id = self._get_preferred_contract(self.partner_id)

        if not self.contract_id:
            self.client_service_id = False
            return {
                'warning': {
                    'title': 'Contrato activo requerido',
                    'message': f"El cliente '{self.partner_id.name}' no tiene contrato activo.",
                }
            }

        if not self.client_service_id or self.client_service_id.partner_id != self.partner_id:
            self.client_service_id = self._find_client_service_for_contract(self.contract_id)

        self._apply_next_period_for_new_record()

        self._sync_payment_defaults()

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            return
        self.partner_id = self.contract_id.partner_id
        self.client_service_id = self._find_client_service_for_contract(self.contract_id) or False

        self._apply_next_period_for_new_record()

        self._sync_payment_defaults()

    @api.onchange('monto_a_cobrar')
    def _onchange_monto_a_cobrar(self):
        # Mantiene monto pagado precargado con el monto del plan/cobro.
        if self.monto_a_cobrar:
            self.monto_pagado = self.monto_a_cobrar

    @api.onchange('client_service_id')
    def _onchange_client_service_id(self):
        if not self.client_service_id:
            return
        self.partner_id = self.client_service_id.partner_id
        if not self.contract_id or self.contract_id.partner_id != self.partner_id:
            self.contract_id = self._find_contract_for_service(self.client_service_id)

        self._apply_next_period_for_new_record()

        self._sync_payment_defaults()

    def _get_preferred_contract(self, partner):
        Contract = self.env['customer.contract']
        contracts = Contract.search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active'),
        ], order='contract_date desc, id desc')
        if not contracts:
            return False
        return contracts[0]

    def _find_client_service_for_contract(self, contract):
        if not contract:
            return False
        ClientService = self.env['wigo.ftth.client.service']

        if contract.lead_id:
            svc = ClientService.search([('lead_id', '=', contract.lead_id.id)], limit=1)
            if svc:
                return svc

        if contract.name:
            svc = ClientService.search([('codigo_cliente', '=', contract.name)], limit=1)
            if svc:
                return svc

        svc = ClientService.search([
            ('partner_id', '=', contract.partner_id.id),
            ('plan_id', '=', contract.plan_id.id),
        ], limit=1)
        return svc or ClientService.search([('partner_id', '=', contract.partner_id.id)], limit=1)

    def _find_contract_for_service(self, service):
        if not service:
            return False
        Contract = self.env['customer.contract']

        domain_base = [
            ('partner_id', '=', service.partner_id.id),
            ('state', '=', 'active'),
        ]

        if service.lead_id:
            contract = Contract.search(domain_base + [('lead_id', '=', service.lead_id.id)], limit=1)
            if contract:
                return contract

        contract = Contract.search(domain_base + [('name', '=', service.codigo_cliente)], limit=1)
        if contract:
            return contract

        if service.plan_id:
            contract = Contract.search(domain_base + [('plan_id', '=', service.plan_id.id)], limit=1)
            if contract:
                return contract

        return Contract.search(domain_base, order='contract_date desc, id desc', limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        Contract = self.env['customer.contract']
        ClientService = self.env['wigo.ftth.client.service']
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            contract_id = vals.get('contract_id')
            service_id = vals.get('client_service_id')

            if partner_id and not contract_id:
                partner = self.env['res.partner'].browse(partner_id)
                contract = self._get_preferred_contract(partner)
                if contract:
                    vals['contract_id'] = contract.id
                    contract_id = contract.id
                else:
                    raise ValidationError(
                        f"El cliente '{partner.name}' no tiene contrato activo."
                    )

            if contract_id and not service_id:
                contract = Contract.browse(contract_id)
                service = self._find_client_service_for_contract(contract)
                if service:
                    vals['client_service_id'] = service.id
                    service_id = service.id

            if service_id and not partner_id:
                service = ClientService.browse(service_id)
                vals['partner_id'] = service.partner_id.id

            if not vals.get('mes') or not vals.get('anio'):
                mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                    contract=Contract.browse(contract_id) if contract_id else None,
                    client_service=ClientService.browse(service_id) if service_id else None,
                    partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
                )
                vals.setdefault('mes', mes_sugerido)
                vals.setdefault('anio', anio_sugerido)

            if not vals.get('fecha_pago'):
                vals['fecha_pago'] = fields.Date.context_today(self)

            if not vals.get('mes') or not vals.get('anio'):
                mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                    contract=Contract.browse(contract_id) if contract_id else None,
                    client_service=ClientService.browse(service_id) if service_id else None,
                    partner=self.env['res.partner'].browse(partner_id) if partner_id else None,
                )
                vals['mes'] = mes_sugerido
                vals['anio'] = anio_sugerido

        records = super().create(vals_list)
        records._sync_payment_defaults()
        records._recompute_contract_mora()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('estado_pago', 'monto_pagado', 'contract_id', 'mes', 'anio')):
            self._recompute_contract_mora()
        return res

    def action_open_contract_crm(self):
        self.ensure_one()
        lead = self._get_won_lead_for_contract()
        if not lead:
            raise UserError(
                'No se encontró un lead ganado de CRM para este contrato/cliente.'
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM - Cliente Ganado',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': lead.id,
            'target': 'current',
        }

    def _get_won_lead_for_contract(self):
        self.ensure_one()
        Lead = self.env['crm.lead']

        if self.contract_id and self.contract_id.lead_id and self.contract_id.lead_id.stage_id.is_won:
            return self.contract_id.lead_id

        domain = [('stage_id.is_won', '=', True)]
        if self.contract_id:
            domain = [('contract_id', '=', self.contract_id.id)] + domain
        elif self.partner_id:
            domain = [('partner_id', '=', self.partner_id.id)] + domain

        lead = Lead.search(domain, order='write_date desc, id desc', limit=1)
        if lead:
            return lead

        if self.partner_id:
            return Lead.search([
                ('partner_id', '=', self.partner_id.id),
                ('stage_id.is_won', '=', True),
            ], order='write_date desc, id desc', limit=1)

        return False

    # ─────────────────────────────────────────────────────────────
    # Business logic
    # ─────────────────────────────────────────────────────────────
    def action_registrar_pago(self):
        """Marcar como pagado y notificar a técnica si había suspensión pendiente."""
        for rec in self:
            if not rec.monto_pagado or not rec.fecha_pago:
                raise ValidationError(
                    'Debe ingresar el monto pagado y la fecha de pago antes de confirmar.'
                )
            if rec.monto_pagado >= rec.monto_a_cobrar:
                rec.estado_pago = 'al_dia'
            else:
                rec.estado_pago = 'deuda_parcial'

            # Actualizar estado_pago en la ficha del servicio
            svc = rec.client_service_id
            if svc:
                svc.estado_pago = rec.estado_pago
                # Si el servicio estaba suspendido → notificar a técnica para reactivar
                if svc.estado_servicio == 'suspended':
                    svc.message_post(
                        body=(
                            f"✅ <b>Pago registrado por cobranza.</b> "
                            f"Cliente <b>{svc.codigo_cliente}</b> pagó Bs. {rec.monto_pagado:.2f} "
                            f"({rec.periodo}). "
                            f"<b>Proceder con la REACTIVACIÓN del servicio en la OLT.</b>"
                        ),
                        subtype_xmlid='mail.mt_comment',
                        partner_ids=self._get_tech_partner_ids(),
                    )
            rec.message_post(
                body=f"Pago de Bs. {rec.monto_pagado:.2f} registrado vía {dict(rec._fields['canal_pago'].selection).get(rec.canal_pago, '')}."
            )
        self._recompute_contract_mora()

    def _recompute_contract_mora(self):
        """
        Regla de negocio: con 3 o más meses sin pago en un contrato,
        todos los pendientes del contrato pasan a mora.
        """
        contracts = self.mapped('contract_id').filtered(lambda c: c)
        if not contracts:
            return

        for contract in contracts:
            pagos = self.search([
                ('contract_id', '=', contract.id),
            ])
            unpaid = pagos.filtered(lambda p: p.estado_pago in ('pendiente', 'deuda_parcial', 'mora'))

            if len(unpaid) >= 3:
                for rec in unpaid:
                    if rec.estado_pago != 'mora':
                        rec.estado_pago = 'mora'

                latest = unpaid.sorted(
                    key=lambda r: (r.anio or 0, int(r.mes or 0), r.id),
                    reverse=True,
                )[:1]
                latest_rec = latest and latest[0] or False
                service = latest_rec.client_service_id if latest_rec else self._find_client_service_for_contract(contract)
                if service:
                    vals = {'estado_pago': 'mora'}
                    if 'estado_servicio' in service._fields and service.estado_servicio != 'baja':
                        vals['estado_servicio'] = 'suspended'
                    service.write(vals)

    def action_marcar_mora(self):
        """Marcar cliente en mora y notificar a técnica para suspensión."""
        for rec in self:
            rec.estado_pago = 'mora'
            svc = rec.client_service_id
            if svc:
                svc.estado_pago = 'mora'
                svc.message_post(
                    body=(
                        f"🔴 <b>Cliente en MORA.</b> "
                        f"Código: <b>{svc.codigo_cliente}</b> — {svc.partner_id.name}. "
                        f"Período adeudado: {rec.periodo}. "
                        f"<b>Contabilidad instruye: proceder con la SUSPENSIÓN del servicio en la OLT.</b>"
                    ),
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=self._get_tech_partner_ids(),
                )

    def action_instruir_baja(self):
        """Instruir baja definitiva al área técnica."""
        for rec in self:
            rec.estado_pago = 'baja_definitiva'
            svc = rec.client_service_id
            if svc:
                svc.estado_pago = 'baja_definitiva'
                svc.estado_servicio = 'baja'
                svc.fecha_baja = date.today()
                svc.message_post(
                    body=(
                        f"⛔ <b>BAJA DEFINITIVA instruida por Contabilidad.</b> "
                        f"Cliente: <b>{svc.codigo_cliente}</b> — {svc.partner_id.name}. "
                        f"<b>Área Técnica: retirar equipo ONU y actualizar estado en sistema.</b>"
                    ),
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=self._get_tech_partner_ids(),
                )

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def _get_tech_partner_ids(self):
        """Retorna los partner_ids de usuarios del grupo técnico FTTH."""
        group = self.env.ref('wigo_ftth.group_ftth_tech', raise_if_not_found=False)
        if not group:
            return []
        return group.users.mapped('partner_id').ids

    def _get_comprobante_url(self, download=False):
        self.ensure_one()
        if not self.comprobante_adjunto:
            raise UserError('No hay comprobante adjunto para mostrar.')

        return (
            f"/web/content?model=wigo.pago.estado&id={self.id}"
            f"&field=comprobante_adjunto&filename_field=comprobante_adjunto_fname"
            f"&download={'true' if download else 'false'}"
        )

    def action_ver_comprobante(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_comprobante_url(download=False),
            'target': 'new',
        }

    def action_descargar_comprobante(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_comprobante_url(download=True),
            'target': 'self',
        }

    # ─────────────────────────────────────────────────────────────
    # Cron actions
    # ─────────────────────────────────────────────────────────────
    @api.model
    def cron_alertar_mora_dia1(self):
        """
        Corre el día 1 de cada mes.
        Crea registros pendientes para todos los clientes activos del mes nuevo
        y notifica a cobranza.
        """
        hoy = date.today()
        mes_actual = str(hoy.month)
        anio_actual = hoy.year

        contracts_activos = self.env['customer.contract'].search([
            ('state', '=', 'active'),
        ])

        creados = 0
        for contract in contracts_activos:
            svc = self._find_client_service_for_contract(contract)
            existente = self.search([
                ('contract_id', '=', contract.id),
                ('mes', '=', mes_actual),
                ('anio', '=', anio_actual),
            ], limit=1)
            if not existente:
                vals = {
                    'partner_id': contract.partner_id.id,
                    'contract_id': contract.id,
                    'mes': mes_actual,
                    'anio': anio_actual,
                    'estado_pago': 'pendiente',
                }
                if svc:
                    vals['client_service_id'] = svc.id
                self.create(vals)
                creados += 1

        # Notificar a grupo cobranza
        cobranza_group = self.env.ref('wigo_cobranza.group_cobranza', raise_if_not_found=False)
        if cobranza_group and creados:
            partners = cobranza_group.users.mapped('partner_id')
            if partners:
                self.env['mail.message'].create({
                    'message_type': 'notification',
                    'body': (
                        f"📋 Se generaron <b>{creados}</b> registros de cobro pendientes "
                        f"para el período {hoy.strftime('%B %Y')}. "
                        f"Por favor inicie la gestión de cobro."
                    ),
                    'partner_ids': partners.ids,
                    'model': 'wigo.pago.estado',
                    'res_id': False,
                })

    @api.model
    def action_open_registros_cobro(self):
        self._ensure_current_month_records()
        return self.env.ref('wigo_cobranza.action_pago_estado').read()[0]

    @api.model
    def _ensure_current_month_records(self):
        hoy = date.today()
        mes_actual = str(hoy.month)
        anio_actual = hoy.year
        contracts_activos = self.env['customer.contract'].search([('state', '=', 'active')])

        for contract in contracts_activos:
            existente = self.search([
                ('contract_id', '=', contract.id),
                ('mes', '=', mes_actual),
                ('anio', '=', anio_actual),
            ], limit=1)
            if existente:
                continue

            service = self._find_client_service_for_contract(contract)
            vals = {
                'partner_id': contract.partner_id.id,
                'contract_id': contract.id,
                'mes': mes_actual,
                'anio': anio_actual,
                'estado_pago': 'pendiente',
            }
            if service:
                vals['client_service_id'] = service.id
            self.create(vals)

    @api.model
    def cron_alertar_suspension(self):
        """
        Corre el día 1 de cada mes.
        Identifica clientes que llevan 1 mes sin pagar y notifica a cobranza
        para que instruyan la suspensión.
        """
        hoy = date.today()
        # Buscar el mes anterior
        if hoy.month == 1:
            mes_mora = '12'
            anio_mora = hoy.year - 1
        else:
            mes_mora = str(hoy.month - 1)
            anio_mora = hoy.year

        registros_mora = self.search([
            ('mes', '=', mes_mora),
            ('anio', '=', anio_mora),
            ('estado_pago', 'in', ['pendiente', 'mora']),
        ])

        for rec in registros_mora:
            if rec.estado_pago != 'mora':
                rec.estado_pago = 'mora'
            svc = rec.client_service_id
            if svc and svc.estado_pago != 'mora':
                svc.estado_pago = 'mora'

        # Notificar a cobranza
        cobranza_group = self.env.ref('wigo_cobranza.group_cobranza', raise_if_not_found=False)
        if cobranza_group and registros_mora:
            partners = cobranza_group.users.mapped('partner_id')
            if partners:
                self.env['mail.message'].create({
                    'message_type': 'notification',
                    'body': (
                        f"⚠️ <b>{len(registros_mora)} clientes en mora</b> por el período "
                        f"{dict(self._fields['mes'].selection).get(mes_mora, mes_mora)} {anio_mora}. "
                        f"Revisar el reporte <i>Clientes a Suspender Hoy</i> y proceder."
                    ),
                    'partner_ids': partners.ids,
                    'model': 'wigo.pago.estado',
                    'res_id': False,
                })
