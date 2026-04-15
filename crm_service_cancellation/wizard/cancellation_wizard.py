# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


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

    @api.depends('contract_id')
    def _compute_contract_code(self):
        for rec in self:
            rec.contract_code = rec.contract_id.name if rec.contract_id else ''

    # ─── Motivo de baja (catálogo editable) ──────────────────────────────────
    reason_id = fields.Many2one(
        'crm.cancellation.reason',
        string='Motivo de baja',
        required=True,
    )
    motivo_detalle = fields.Text(string='Detalle del motivo')
    fecha_baja = fields.Date(
        string='Fecha de baja',
        required=True,
        default=fields.Date.today,
    )

    # ─── Datos del ONU ───────────────────────────────────────────────────────
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
            'onu_serial':                     self.onu_serial or '',
            'onu_mac':                        self.onu_mac or '',
            'onu_modelo':                     self.onu_modelo or '',
            'meses_deuda':                    self.meses_deuda,
            'monto_deuda':                    self.monto_deuda if self.meses_deuda > 0 else 0.0,
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
        return {'type': 'ir.actions.act_window_close'}
