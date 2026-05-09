# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class ServiceCancellationWizard(models.TransientModel):
    """
    Wizard de baja de servicio.
    Se abre desde el botón 'Dar de baja' en el lead ganado.
    Al confirmar:
      1. Crea un registro persistente en service.cancellation
      2. Termina el contrato vinculado (si aplica)
      3. Mueve el lead a la etapa "Bajas" (NO a Perdido)
      4. Crea actividad de recojo de ONU
    """
    _name = 'service.cancellation.wizard'
    _description = 'Wizard de Baja de Servicio'

    # ─── Relaciones ───────────────────────────────────────────────────────────
    lead_id = fields.Many2one('crm.lead', string='Oportunidad', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, readonly=True)
    contract_id = fields.Many2one('customer.contract', string='Contrato', readonly=True)
    plan_id = fields.Many2one('internet.plan', string='Plan contratado', readonly=True)

    # ─── Datos del cliente (solo lectura, autorellenados) ─────────────────────
    codigo_cliente = fields.Char(string='Código de cliente', readonly=True)
    ci_cliente = fields.Char(string='Carnet de identidad', readonly=True)
    contract_code = fields.Char(
        string='Código de contrato',
        compute='_compute_contract_code',
    )
    contract_state = fields.Selection(
        related='contract_id.state',
        string='Estado del contrato',
        readonly=True,
    )

    # ─── Snapshot técnico FTTH (solo lectura, autocompletado) ───────────────
    ftth_client_service_id = fields.Many2one(
        'wigo.ftth.client.service',
        string='Ficha técnica FTTH',
        readonly=True,
    )
    ftth_estado_servicio = fields.Selection(
        [
            ('active', 'Activo'),
            ('suspended', 'Suspendido'),
            ('corte', 'En corte (mora)'),
            ('baja', 'Dado de baja'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado servicio FTTH',
        readonly=True,
    )
    ftth_fecha_instalacion = fields.Date(string='Fecha instalación FTTH', readonly=True)
    ftth_nodo = fields.Char(string='Nodo FTTH', readonly=True)
    ftth_olt = fields.Char(string='OLT FTTH', readonly=True)
    ftth_olt_port = fields.Char(string='Puerto OLT FTTH', readonly=True)
    ftth_subinterface = fields.Char(string='Subinterfaz FTTH', readonly=True)
    ftth_nap = fields.Char(string='NAP FTTH', readonly=True)
    ftth_nap_port = fields.Char(string='Puerto NAP FTTH', readonly=True)

    @api.depends('contract_id')
    def _compute_contract_code(self):
        for rec in self:
            rec.contract_code = rec.contract_id.name if rec.contract_id else ''

    # ─── Motivo de baja (catálogo editable) ──────────────────────────────────
    reason_id = fields.Many2one(
        'crm.cancellation.reason',
        string='Motivo de baja',
    )
    motivo_detalle = fields.Text(string='Detalle del motivo')
    fecha_baja = fields.Date(
        string='Fecha de baja',
        default=fields.Date.today,
    )

    # ─── Datos del ONU ───────────────────────────────────────────────────────
    onu_equipo = fields.Char(string='Equipo', readonly=True)
    onu_rotulo = fields.Char(string='Rótulo / Etiqueta')
    onu_marca = fields.Char(string='Marca', readonly=True)
    onu_serial = fields.Char(string='N° de serie ONU')
    onu_mac = fields.Char(string='MAC ONU')
    onu_modelo = fields.Char(string='Modelo ONU')

    # ─── Deuda ───────────────────────────────────────────────────────────────
    meses_deuda = fields.Integer(
        string='Meses de deuda',
        default=0,
        help='Número de meses que el cliente adeuda. 0 = sin deuda.',
    )
    monto_deuda = fields.Monetary(
        string='Monto total de deuda',
        currency_field='currency_id',
        help='Se completará automáticamente cuando haya integración con facturación.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    cobranza_estado_pago = fields.Selection(
        [
            ('pagado', 'Cobrado / Al día'),
            ('pendiente', 'Pendiente'),
            ('mora', 'En mora'),
        ],
        string='Estado de cobranza',
        readonly=True,
    )
    cobranza_ultimo_periodo_pagado = fields.Char(string='Último mes pagado', readonly=True)
    cobranza_ultimo_pago_fecha = fields.Date(string='Fecha de pago', readonly=True)
    cobranza_ultimo_monto_pagado = fields.Monetary(string='Monto pagado', currency_field='currency_id', readonly=True)
    
    cobranza_monto_deuda_total = fields.Monetary(string='Monto que debe', currency_field='currency_id', readonly=True)
    cobranza_dias_retraso = fields.Integer(string='Días de retraso', readonly=True)

    # ─── Acción sobre contrato ────────────────────────────────────────────────
    terminar_contrato = fields.Boolean(
        string='Terminar contrato',
        default=True,
        help='Marca el contrato como Finalizado al confirmar la baja.',
    )

    # ─── Notas ────────────────────────────────────────────────────────────────
    notas = fields.Text(string='Notas internas')

    # ─── Validaciones ─────────────────────────────────────────────────────────
    @api.constrains('meses_deuda', 'monto_deuda')
    def _check_deuda(self):
        for rec in self:
            if rec.meses_deuda > 0 and rec.monto_deuda <= 0:
                raise ValidationError(
                    'Si hay meses de deuda, debe ingresar el monto total mayor a 0.'
                )

    @api.constrains('fecha_baja')
    def _check_fecha_baja(self):
        for rec in self:
            if rec.fecha_baja and rec.fecha_baja > fields.Date.today():
                raise ValidationError('La fecha de baja no puede ser una fecha futura.')

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if values.get('partner_id') or values.get('contract_id') or values.get('lead_id'):
            temp = self.new(values)
            temp._sync_ftth_and_cobranza_snapshot()
            values.update(temp._convert_to_write(temp._cache))
        return values

    @api.onchange('partner_id', 'contract_id', 'lead_id')
    def _onchange_autofill_ftth_cobranza(self):
        self._sync_ftth_and_cobranza_snapshot()

    def _find_client_service(self):
        self.ensure_one()
        ClientService = self.env['wigo.ftth.client.service']

        if self.contract_id and self.contract_id.lead_id:
            service = ClientService.search([('lead_id', '=', self.contract_id.lead_id.id)], limit=1)
            if service:
                return service

        if self.lead_id:
            service = ClientService.search([('lead_id', '=', self.lead_id.id)], limit=1)
            if service:
                return service

        if self.contract_id and self.contract_id.name:
            service = ClientService.search([('codigo_cliente', '=', self.contract_id.name)], limit=1)
            if service:
                return service

        if self.partner_id:
            service = ClientService.search([
                ('partner_id', '=', self.partner_id.id),
            ], order='write_date desc, id desc', limit=1)
            if service:
                return service
        return False

    def _build_cobranza_snapshot(self, service):
        self.ensure_one()
        Payment = self.env['wigo.pago.estado']
        records = Payment.browse()

        if service:
            records |= Payment.search([('client_service_id', '=', service.id)])
        if self.contract_id:
            records |= Payment.search([('contract_id', '=', self.contract_id.id)])
        if not records and self.partner_id:
            records |= Payment.search([('partner_id', '=', self.partner_id.id)])

        unpaid_states = ('pendiente', 'deuda_parcial', 'mora')
        unpaid = records.filtered(lambda p: p.estado_pago in unpaid_states)

        saldo_total = 0.0
        for pay in unpaid:
            saldo = max((pay.monto_a_cobrar or 0.0) - (pay.monto_pagado or 0.0), 0.0)
            saldo_total += saldo

        ordered_unpaid = unpaid.sorted(key=lambda p: ((p.anio or 0), int(p.mes or 0), p.id or 0))
        resumen_lineas = []
        for pay in ordered_unpaid:
            resumen_lineas.append(
                f"- {pay.periodo or (str(pay.mes) + '/' + str(pay.anio))}: "
                f"{pay.estado_pago} | saldo {max((pay.monto_a_cobrar or 0.0) - (pay.monto_pagado or 0.0), 0.0):.2f}"
            )

        # Determine status
        if records.filtered(lambda p: p.estado_pago == 'mora'):
            estado_actual = 'mora'
        elif records.filtered(lambda p: p.estado_pago == 'pendiente'):
            estado_actual = 'pendiente'
        else:
            estado_actual = 'pagado'
            
        # Last paid record
        last_paid = records.filtered(lambda p: p.estado_pago == 'pagado' and p.fecha_pago)
        latest_paid_record = last_paid.sorted(key=lambda p: p.fecha_pago, reverse=True)[:1] if last_paid else False

        # Debt and days late
        en_mora_records = records.filtered(lambda p: p.estado_pago == 'mora')
        max_dias_atraso = max(en_mora_records.mapped('dias_atraso')) if en_mora_records else 0

        return {
            'cobranza_estado_pago': estado_actual,
            'cobranza_ultimo_periodo_pagado': latest_paid_record.periodo if latest_paid_record else '',
            'cobranza_ultimo_pago_fecha': latest_paid_record.fecha_pago if latest_paid_record else False,
            'cobranza_ultimo_monto_pagado': latest_paid_record.monto_pagado if latest_paid_record else 0.0,
            'cobranza_monto_deuda_total': saldo_total,
            'cobranza_dias_retraso': max_dias_atraso,
            'meses_deuda': len(unpaid),
            'monto_deuda': saldo_total,
        }

    def _sync_ftth_and_cobranza_snapshot(self):
        for wizard in self:
            service = wizard._find_client_service()
            wizard.ftth_client_service_id = service
            wizard.ftth_estado_servicio = service.estado_servicio if service else False
            wizard.ftth_fecha_instalacion = service.fecha_instalacion if service else False
            wizard.ftth_nodo = service.nodo_id.name if service and service.nodo_id else False
            wizard.ftth_olt = service.olt_id.display_name if service and service.olt_id else False
            wizard.ftth_olt_port = (
                service.olt_port_id.interface_port
                or (f"Puerto {service.olt_port_id.port_number}" if service.olt_port_id.port_number else False)
            ) if service and service.olt_port_id else False
            wizard.ftth_subinterface = (
                service.subinterface_id.code
                or service.subinterface_id.display_name
            ) if service and service.subinterface_id else False
            wizard.ftth_nap = (
                getattr(service.box_id, 'identifier', False)
                or getattr(service.box_id, 'identificador', False)
                or service.box_id.display_name
            ) if service and service.box_id else False
            wizard.ftth_nap_port = (
                str(getattr(service.box_port_id, 'port_number', False) or getattr(service.box_port_id, 'numero_puerto', False))
                if service and service.box_port_id and (getattr(service.box_port_id, 'port_number', False) or getattr(service.box_port_id, 'numero_puerto', False))
                else False
            )

            onu = False
            if service:
                onu = service.onu_id or (service.subinterface_id.onu_id if service.subinterface_id else False)

            if onu:
                wizard.onu_equipo = 'ONU/ONT'
                wizard.onu_rotulo = onu.rotulo or wizard.onu_rotulo
                wizard.onu_marca = onu.marca or (onu.marca_id.name if onu.marca_id else wizard.onu_marca)
                wizard.onu_serial = onu.serial_number or wizard.onu_serial
                wizard.onu_modelo = onu.modelo or (onu.modelo_id.name if onu.modelo_id else wizard.onu_modelo)
            else:
                wizard.onu_equipo = wizard.onu_equipo or 'ONU/ONT'

            cobranza_vals = wizard._build_cobranza_snapshot(service)
            wizard.update(cobranza_vals)

    # ─── Helpers ──────────────────────────────────────────────────────────────
    def _get_or_create_baja_stage(self):
        """
        Busca o crea la etapa 'Bajas' en el CRM.
        Esta etapa NO es ganado ni perdido: es una columna propia para clientes dados de baja.
        """
        Stage = self.env['crm.stage']
        stage = Stage.search([('name', 'ilike', 'Bajas')], limit=1)
        if not stage:
            stage = Stage.create({
                'name': 'Bajas',
                'sequence': 99,
                'is_won': False,
                'requirements': 'Cliente dado de baja de servicio',
            })
        return stage

    def _create_onu_activity(self):
        """
        Crea una actividad de tipo 'Tarea' en el lead
        para recordar el recojo del equipo ONU si se registró información.
        """
        if not (self.onu_serial or self.onu_mac or self.onu_modelo):
            return
        ActivityType = self.env['mail.activity.type']
        act_type = ActivityType.search([('name', 'ilike', 'Tarea')], limit=1)
        if not act_type:
            act_type = ActivityType.search([], limit=1)
        if act_type:
            self.lead_id.activity_schedule(
                activity_type_id=act_type.id,
                summary='Recoger equipo ONU del domicilio del cliente',
                note=(
                    f'El ONU fue dejado en el domicilio del cliente al dar de baja.<br/>'
                    f'Modelo: {self.onu_modelo or "N/D"} | '
                    f'Serial: {self.onu_serial or "N/D"} | '
                    f'MAC: {self.onu_mac or "N/D"}'
                ),
                date_deadline=fields.Date.today(),
            )

    def _mirror_lead_activities(self, cancellation):
        """Replica en la baja las actividades ya registradas en el lead."""
        if not self.lead_id or not cancellation:
            return

        activity_model = self.env['mail.activity']
        ir_model = self.env['ir.model']
        cancellation_model_id = ir_model._get(cancellation._name).id

        existing_keys = {
            (
                activity.activity_type_id.id,
                activity.summary or '',
                activity.note or '',
                activity.date_deadline,
                activity.user_id.id,
            )
            for activity in cancellation.activity_ids
        }

        for activity in self.lead_id.activity_ids:
            if getattr(activity, 'is_post_sale_activity', False):
                continue
            activity_key = (
                activity.activity_type_id.id,
                activity.summary or '',
                activity.note or '',
                activity.date_deadline,
                activity.user_id.id,
            )
            if activity_key in existing_keys:
                continue

            activity_model.create({
                'activity_type_id': activity.activity_type_id.id,
                'summary': activity.summary,
                'note': activity.note,
                'date_deadline': activity.date_deadline,
                'user_id': activity.user_id.id or self.env.user.id,
                'res_model_id': cancellation_model_id,
                'res_id': cancellation.id,
            })

    # ─── Confirmar baja ───────────────────────────────────────────────────────
    def action_confirm_cancellation(self):
        self.ensure_one()

        if not self.reason_id:
            raise ValidationError('Debe seleccionar un motivo de baja antes de confirmar.')
        if not self.fecha_baja:
            raise ValidationError('Debe indicar la fecha de baja antes de confirmar.')

        # Estado del contrato antes de terminarlo
        contract_state_label = ''
        if self.contract_id:
            state_map = dict(self.contract_id._fields['state'].selection)
            contract_state_label = state_map.get(self.contract_id.state, '')

        # 1. Crear registro histórico de baja
        cancellation = self.env['service.cancellation'].create({
            'lead_id':                        self.lead_id.id,
            'partner_id':                     self.partner_id.id,
            'contract_id':                    self.contract_id.id if self.contract_id else False,
            'codigo_cliente':                 self.codigo_cliente or '',
            'ci_cliente':                     self.ci_cliente or '',
            'plan_id':                        self.plan_id.id if self.plan_id else False,
            'reason_id':                      self.reason_id.id,
            'motivo_detalle':                 self.motivo_detalle or '',
            'fecha_baja':                     self.fecha_baja,
            'ftth_client_service_id':         self.ftth_client_service_id.id if self.ftth_client_service_id else False,
            'ftth_estado_servicio':           self.ftth_estado_servicio or False,
            'ftth_fecha_instalacion':         self.ftth_fecha_instalacion or False,
            'ftth_nodo':                      self.ftth_nodo or '',
            'ftth_olt':                       self.ftth_olt or '',
            'ftth_olt_port':                  self.ftth_olt_port or '',
            'ftth_subinterface':              self.ftth_subinterface or '',
            'ftth_nap':                       self.ftth_nap or '',
            'ftth_nap_port':                  self.ftth_nap_port or '',
            'onu_equipo':                     self.onu_equipo or '',
            'onu_rotulo':                     self.onu_rotulo or '',
            'onu_marca':                      self.onu_marca or '',
            'onu_serial':                     self.onu_serial or '',
            'onu_mac':                        self.onu_mac or '',
            'onu_modelo':                     self.onu_modelo or '',
            'meses_deuda':                    self.meses_deuda,
            'monto_deuda':                    self.monto_deuda if self.meses_deuda > 0 else 0.0,
            'cobranza_estado_pago':           self.cobranza_estado_pago or False,
            'cobranza_ultimo_periodo_pagado': self.cobranza_ultimo_periodo_pagado or '',
            'cobranza_ultimo_pago_fecha':     self.cobranza_ultimo_pago_fecha or False,
            'cobranza_ultimo_monto_pagado':   self.cobranza_ultimo_monto_pagado or 0.0,
            'cobranza_monto_deuda_total':     self.cobranza_monto_deuda_total or 0.0,
            'cobranza_dias_retraso':          self.cobranza_dias_retraso or 0,
            'contrato_terminado':             self.terminar_contrato,
            'contract_state_at_cancellation': contract_state_label,
            'notas':                          self.notas or '',
        })

        # 2. Terminar contrato vinculado si se indicó
        if self.terminar_contrato and self.contract_id:
            if self.contract_id.state not in ('terminated',):
                try:
                    self.contract_id.action_terminate()
                except Exception:
                    self.contract_id.write({'state': 'terminated'})

        # 3. Mover el lead a la etapa "Bajas" (NO marcar como perdido)
        baja_stage = self._get_or_create_baja_stage()
        self.lead_id.write({
            'stage_id': baja_stage.id,
        })

        # 3.5. Crear automáticamente la orden de trabajo FTTH (Baja / Retiro) si corresponde
        if self.ftth_client_service_id:
            WoModel = self.env['wigo.ftth.work.order']
            motivo_str = self.reason_id.name
            if self.motivo_detalle:
                motivo_str += f" - {self.motivo_detalle}"

            wo_vals = {
                'work_type': 'deactivation',
                'state': 'pending',
                'contract_id': self.contract_id.id if self.contract_id else False,
                'lead_id': self.lead_id.id if self.lead_id else False,
                'client_service_id': self.ftth_client_service_id.id,
                'cancellation_reason': motivo_str,
            }
            if self.contract_id:
                wo_vals.update({
                    'address': self.contract_id.address,
                    'contact_phone': self.contract_id.mobile,
                    'location_link': self.contract_id.location_link,
                })
            WoModel.with_context(allow_deactivation_create=True).create(wo_vals)

        # 4. Crear actividad de recojo de ONU si aplica
        self._create_onu_activity()

        # 4bis. Reflejar en la baja las actividades que ya existen en el lead
        self._mirror_lead_activities(cancellation)

        # 5. Log en el chatter del lead y en la baja
        deuda_txt = (
            f'{self.meses_deuda} mes(es) — {self.monto_deuda} {self.currency_id.name}'
            if self.meses_deuda > 0 else 'Sin deuda'
        )
        msg = (
            f"<b>Baja de servicio registrada</b><br/>"
            f"Motivo: {self.reason_id.name}<br/>"
            f"Fecha de baja: {self.fecha_baja}<br/>"
            f"ONU: {self.onu_modelo or '-'} | Serial: {self.onu_serial or '-'}<br/>"
            f"Deuda: {deuda_txt}<br/>"
        )
        if self.notas:
            msg += f"Notas: {self.notas}"
        self.lead_id.message_post(body=msg, subtype_xmlid='mail.mt_note')
        cancellation.message_post(body=msg, subtype_xmlid='mail.mt_note')

        # 6. Abrir el registro de baja recién creado
        return {
            'type': 'ir.actions.act_window',
            'name': 'Baja de Servicio',
            'res_model': 'service.cancellation',
            'view_mode': 'form',
            'res_id': cancellation.id,
            'target': 'current',
        }

    def action_cancel(self):
        self.ensure_one()
        if self.lead_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Oportunidad',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': self.lead_id.id,
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}

    def action_open_ftth_service(self):
        self.ensure_one()
        if not self.ftth_client_service_id:
            raise UserError('No se encontró una ficha técnica FTTH para este cliente.')
        self._save_wizard_progress()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ficha Técnica FTTH',
            'res_model': 'wigo.ftth.client.service',
            'view_mode': 'form',
            'res_id': self.ftth_client_service_id.id,
            'target': 'current',
        }

    def action_open_cobranza_payments(self):
        self.ensure_one()
        domain = []
        if self.ftth_client_service_id:
            domain = [('client_service_id', '=', self.ftth_client_service_id.id)]
        elif self.contract_id:
            domain = [('contract_id', '=', self.contract_id.id)]
        elif self.partner_id:
            domain = [('partner_id', '=', self.partner_id.id)]

        if not domain:
            raise UserError('No hay referencia de cliente/contrato/servicio para abrir pagos de cobranza.')

        self._save_wizard_progress()

        list_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_list_new', raise_if_not_found=False)
        form_view = self.env.ref('wigo_cobranza.view_pago_estado_contract_form_new', raise_if_not_found=False)
        views = []
        if list_view:
            views.append((list_view.id, 'list'))
        if form_view:
            views.append((form_view.id, 'form'))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Cobranza - {self.partner_id.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'views': views or False,
            'domain': domain,
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_contract_id': self.contract_id.id if self.contract_id else False,
                'default_client_service_id': self.ftth_client_service_id.id if self.ftth_client_service_id else False,
            },
            'target': 'current',
        }

    def _save_wizard_progress(self):
        """Persist user-entered fields so browser back restores the latest wizard state."""
        self.ensure_one()
        self.write({
            'reason_id': self.reason_id.id if self.reason_id else False,
            'motivo_detalle': self.motivo_detalle or False,
            'fecha_baja': self.fecha_baja or False,
            'onu_rotulo': self.onu_rotulo or False,
            'onu_serial': self.onu_serial or False,
            'onu_mac': self.onu_mac or False,
            'onu_modelo': self.onu_modelo or False,
            'notas': self.notas or False,
            'terminar_contrato': bool(self.terminar_contrato),
        })
