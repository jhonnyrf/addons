import logging

from html import escape
from markupsafe import Markup

from odoo import models, fields, api
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class WigoIncobrable(models.Model):
    _name = 'wigo.incobrable'
    _description = 'Uncollectible Debt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_declaracion desc'
    _rec_name = 'display_name'

    BOLIVIA_TIMEZONE = 'America/La_Paz'
    AUDIT_DATE_FORMAT = '%d/%m/%Y'
    AUDIT_DATETIME_FORMAT = '%d/%m/%Y %H:%M'

    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        ondelete='restrict', index=True,
    )
    contract_id = fields.Many2one(
        'customer.contract', string='Contrato',
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
        ondelete='restrict',
    )
    suspension_id = fields.Many2one(
        'wigo.ftth.service.suspension', string='Suspensión FTTH',
        ondelete='set null',
    )
    codigo_cliente = fields.Char(
        string='Código CF', compute='_compute_client_data', store=True,
    )
    plan_id = fields.Many2one(
        'internet.plan', string='Plan', compute='_compute_client_data', store=True,
    )
    monto_plan = fields.Float(
        string='Monto del plan (Bs)',
        related='plan_id.price', store=True, readonly=True,
    )
    plan_identifier = fields.Char(
        string='Identificador del plan',
        related='plan_id.plan_identifier', store=True, readonly=True,
    )
    meses_adeudados = fields.Char(
        string='Meses adeudados',
        help='Ej: Enero, Febrero/2026',
    )
    monto_total_adeudado = fields.Float(
        string='Monto total adeudado (Bs)',
    )
    monto_cobrado = fields.Float(
        string='Monto cobrado efectivamente (Bs)',
    )
    diferencia_incobrable = fields.Float(
        string='Monto incobrable definitivo (Bs)',
        compute='_compute_diferencia_incobrable', store=True,
    )
    fecha_declaracion = fields.Date(
        string='Fecha de declaración',
        default=lambda self: fields.Date.context_today(
            self.with_context(tz='America/La_Paz')
        ),
        required=True,
    )
    fecha_baja_servicio = fields.Date(
        string='Fecha baja de servicio',
    )
    state = fields.Selection([
        ('activo', 'En gestión'),
        ('in_cut', 'En corte'),
        ('baja_incobrable', 'Baja - Incobrable'),
        ('recuperado', 'Recuperado'),
    ], string='Estado', default='activo', required=True, index=True)
    observaciones = fields.Text(string='Observaciones')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('partner_id', 'contract_id', 'client_service_id')
    def _compute_client_data(self):
        for rec in self:
            rec.codigo_cliente = (
                rec.contract_id.name or rec.client_service_id.codigo_cliente or False
            )
            rec.plan_id = (
                rec.contract_id.plan_id or rec.client_service_id.plan_id or False
            )

    @api.depends('monto_total_adeudado', 'monto_cobrado')
    def _compute_diferencia_incobrable(self):
        for rec in self:
            rec.diferencia_incobrable = rec.monto_total_adeudado - rec.monto_cobrado

    @api.depends('partner_id', 'meses_adeudados')
    def _compute_display_name(self):
        for rec in self:
            nombre = rec.partner_id.name or ''
            rec.display_name = f"{nombre} -- {rec.meses_adeudados}" if rec.meses_adeudados else nombre

    def _get_bolivia_now(self):
        return fields.Datetime.context_timestamp(
            self.with_context(tz=self.BOLIVIA_TIMEZONE),
            fields.Datetime.now(),
        )

    def _get_bolivia_datetime_string(self):
        return self._get_bolivia_now().strftime(self.AUDIT_DATETIME_FORMAT)

    def _get_bolivia_date(self):
        return fields.Date.context_today(self.with_context(tz=self.BOLIVIA_TIMEZONE))

    def _format_date_value(self, value):
        if not value:
            return '—'
        if hasattr(value, 'strftime'):
            return value.strftime(self.AUDIT_DATE_FORMAT)
        return str(value)

    def _format_money_value(self, value):
        return f"Bs. {float(value or 0.0):.2f}"

    def _get_record_display_value(self, record):
        if not record:
            return '—'
        return record.display_name or record.name or str(record.id)

    def _get_selection_label(self, field_name, value):
        if not value:
            return '—'
        field = self._fields.get(field_name)
        selection = getattr(field, 'selection', None)
        if selection:
            return dict(selection).get(value, str(value))
        return str(value)

    def _get_audit_snapshot(self):
        self.ensure_one()
        return {
            'partner_id': self.partner_id.id,
            'partner_name': self._get_record_display_value(self.partner_id),
            'contract_id': self.contract_id.id,
            'contract_name': self._get_record_display_value(self.contract_id),
            'client_service_id': self.client_service_id.id,
            'client_service_name': self._get_record_display_value(self.client_service_id),
            'suspension_id': self.suspension_id.id,
            'suspension_name': self._get_record_display_value(self.suspension_id),
            'state': self.state,
            'state_label': self._get_selection_label('state', self.state),
            'meses_adeudados': self.meses_adeudados or '',
            'monto_total_adeudado': self.monto_total_adeudado,
            'monto_cobrado': self.monto_cobrado,
            'fecha_declaracion': self.fecha_declaracion,
            'fecha_baja_servicio': self.fecha_baja_servicio,
            'observaciones': self.observaciones or '',
        }

    def _build_audit_changes(self, before):
        self.ensure_one()
        changes = []
        current_service = self.client_service_id

        if before['state'] != self.state:
            changes.append((
                'Estado',
                f"{self._get_selection_label('state', before['state'])} → {self._get_selection_label('state', self.state)}",
            ))
        if before['partner_id'] != self.partner_id.id:
            changes.append(('Cliente', f"{before['partner_name']} → {self._get_record_display_value(self.partner_id)}"))
        if before['contract_id'] != self.contract_id.id:
            changes.append(('Contrato', f"{before['contract_name']} → {self._get_record_display_value(self.contract_id)}"))
        if before['client_service_id'] != self.client_service_id.id:
            changes.append(('Servicio (CF)', f"{before['client_service_name']} → {self._get_record_display_value(current_service)}"))
        if before['suspension_id'] != self.suspension_id.id:
            changes.append(('Suspensión FTTH', f"{before['suspension_name']} → {self._get_record_display_value(self.suspension_id)}"))
        if before['meses_adeudados'] != (self.meses_adeudados or ''):
            changes.append(('Meses adeudados', f"{before['meses_adeudados'] or '—'} → {self.meses_adeudados or '—'}"))
        if before['monto_total_adeudado'] != self.monto_total_adeudado:
            changes.append((
                'Monto total adeudado',
                f"{self._format_money_value(before['monto_total_adeudado'])} → {self._format_money_value(self.monto_total_adeudado)}",
            ))
        if before['monto_cobrado'] != self.monto_cobrado:
            changes.append((
                'Monto cobrado',
                f"{self._format_money_value(before['monto_cobrado'])} → {self._format_money_value(self.monto_cobrado)}",
            ))
        if before['fecha_declaracion'] != self.fecha_declaracion:
            changes.append((
                'Fecha de declaración',
                f"{self._format_date_value(before['fecha_declaracion'])} → {self._format_date_value(self.fecha_declaracion)}",
            ))
        if before['fecha_baja_servicio'] != self.fecha_baja_servicio:
            changes.append((
                'Fecha de baja de servicio',
                f"{self._format_date_value(before['fecha_baja_servicio'])} → {self._format_date_value(self.fecha_baja_servicio)}",
            ))
        if before['observaciones'] != (self.observaciones or ''):
            changes.append(('Observaciones', f"{before['observaciones'] or '—'} → {self.observaciones or '—'}"))

        return changes

    def _build_audit_body(self, title, changes=None, justification=None):
        self.ensure_one()
        body_parts = [f"<b>{escape(title)}</b><br/><br/>"]
        if changes:
            items = ''.join(
                f"<li><b>{escape(label)}:</b> {escape(value)}</li>"
                for label, value in changes
                if value not in (None, '')
            )
            if items:
                body_parts.append(f"<ul>{items}</ul>")
        if justification:
            body_parts.append(f"<b>Justificación:</b><br/>{escape(justification)}<br/><br/>")
        body_parts.append(f"<b>Usuario:</b> {escape(self.env.user.display_name or '')}<br/>")
        body_parts.append(f"<b>Fecha y hora:</b> {escape(self._get_bolivia_datetime_string())}")
        return Markup(''.join(body_parts))

    def _log_audit_event(self, title, changes=None, justification=None):
        details = []
        if changes:
            details.append(', '.join(f'{label}: {value}' for label, value in changes))
        if justification:
            details.append(f'Justificación: {justification}')
        details.append(f"usuario={self.env.user.display_name or ''}")
        details.append(f"fecha_hora={self._get_bolivia_datetime_string()}")
        _logger.info('Incobrable audit | %s | %s', title, ' | '.join(details))

    def _post_audit_message(self, title, changes=None, justification=None):
        self.ensure_one()
        body = self._build_audit_body(title, changes=changes, justification=justification)
        self.with_context(lang='es_BO').message_post(body=body, subtype_xmlid='mail.mt_note')
        self._log_audit_event(title, changes=changes, justification=justification)

    def _get_service_snapshot(self, service):
        if not service:
            return {}
        return {
            'estado_pago': getattr(service, 'estado_pago', False),
            'estado_servicio': getattr(service, 'estado_servicio', False),
            'fecha_baja': getattr(service, 'fecha_baja', False),
        }

    def _build_service_changes(self, before, service):
        if not service:
            return []

        changes = []
        if before.get('estado_pago') != getattr(service, 'estado_pago', False):
            changes.append((
                'Servicio - estado de pago',
                f"{before.get('estado_pago') or '—'} → {getattr(service, 'estado_pago', False) or '—'}",
            ))
        if before.get('estado_servicio') != getattr(service, 'estado_servicio', False):
            changes.append((
                'Servicio - estado',
                f"{before.get('estado_servicio') or '—'} → {getattr(service, 'estado_servicio', False) or '—'}",
            ))
        if before.get('fecha_baja') != getattr(service, 'fecha_baja', False):
            changes.append((
                'Servicio - fecha de baja',
                f"{self._format_date_value(before.get('fecha_baja'))} → {self._format_date_value(getattr(service, 'fecha_baja', False))}",
            ))
        return changes

    def _post_creation_audit(self, origin=None):
        for rec in self:
            changes = [
                ('Cliente', rec._get_record_display_value(rec.partner_id)),
                ('Contrato', rec._get_record_display_value(rec.contract_id)),
                ('Servicio (CF)', rec._get_record_display_value(rec.client_service_id)),
                ('Meses adeudados', rec.meses_adeudados or '—'),
                ('Monto total adeudado', rec._format_money_value(rec.monto_total_adeudado)),
                ('Monto cobrado', rec._format_money_value(rec.monto_cobrado)),
                ('Diferencia incobrable', rec._format_money_value(rec.diferencia_incobrable)),
                ('Estado', rec._get_selection_label('state', rec.state)),
                ('Fecha de declaración', rec._format_date_value(rec.fecha_declaracion)),
            ]
            if rec.fecha_baja_servicio:
                changes.append(('Fecha de baja de servicio', rec._format_date_value(rec.fecha_baja_servicio)))
            if origin:
                changes.append(('Origen', origin))
            rec._post_audit_message('Registro de incobrable creado', changes=changes)

    def _post_write_audit(self, before, extra_changes=None, justification=None, title='Actualización de incobrable'):
        self.ensure_one()
        changes = self._build_audit_changes(before)
        if extra_changes:
            changes.extend(extra_changes)
        if not changes and not justification:
            return
        self._post_audit_message(title, changes=changes, justification=justification)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.env.context.get('skip_incobrable_audit'):
            return records

        origin = self.env.context.get('incobrable_audit_origin')
        records._post_creation_audit(origin=origin)
        return records

    def write(self, vals):
        if self.env.context.get('skip_incobrable_audit'):
            return super().write(vals)

        tracked_fields = {
            'partner_id', 'contract_id', 'client_service_id', 'suspension_id',
            'meses_adeudados', 'monto_total_adeudado', 'monto_cobrado',
            'fecha_declaracion', 'fecha_baja_servicio', 'state', 'observaciones',
        }
        if not any(field in vals for field in tracked_fields):
            return super().write(vals)

        before_snapshots = {rec.id: rec._get_audit_snapshot() for rec in self}
        res = super().write(vals)

        for rec in self:
            before = before_snapshots.get(rec.id)
            if not before:
                continue
            rec._post_write_audit(before)

        return res

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
            before = rec._get_audit_snapshot()
            suspension = rec._get_or_create_suspension_record()
            values = {'state': 'in_cut'}
            if suspension:
                values['suspension_id'] = suspension.id
            rec.with_context(skip_incobrable_audit=True).write(values)
            rec._post_write_audit(before, title='Actualización de estado a corte')

    def _get_or_create_suspension_record(self):
        self.ensure_one()
        Suspension = self.env['wigo.ftth.service.suspension'].sudo()
        domain = [('contract_id', '=', self.contract_id.id)]
        if self.client_service_id:
            domain.append(('client_service_id', '=', self.client_service_id.id))

        suspension = Suspension.search(
            domain + [('state', 'in', ('pendiente', 'in_cut'))],
            order='fecha_registro desc, id desc', limit=1,
        )
        if suspension:
            if suspension.state == 'pendiente':
                suspension.action_marcar_en_corte()
                if 'fecha_corte' in suspension._fields:
                    suspension.sudo().write({'fecha_corte': self._get_bolivia_date()})
            elif suspension.state == 'in_cut' and not suspension.fecha_corte:
                if 'fecha_corte' in suspension._fields:
                    suspension.sudo().write({'fecha_corte': self._get_bolivia_date()})
                elif hasattr(suspension, '_ensure_cut_date'):
                    suspension._ensure_cut_date()
            return suspension

        vals = {
            'contract_id': self.contract_id.id,
            'client_service_id': self.client_service_id.id if self.client_service_id else False,
            'state': 'pendiente',
            'fecha_corte': self._get_bolivia_date(),
        }
        return Suspension.create(vals)

    def action_marcar_baja_incobrable(self):
        for rec in self:
            before = rec._get_audit_snapshot()
            service_before = rec._get_service_snapshot(rec.client_service_id)
            fecha_baja = rec.fecha_baja_servicio or rec._get_bolivia_date()
            rec.with_context(skip_incobrable_audit=True).write({
                'state': 'baja_incobrable',
                'fecha_baja_servicio': fecha_baja,
            })
            service = rec.client_service_id.sudo() if rec.client_service_id else False
            if service:
                service_vals = {}
                if getattr(service, 'estado_pago', False) != 'baja_definitiva':
                    service_vals['estado_pago'] = 'baja_definitiva'
                if 'estado_servicio' in service._fields and getattr(service, 'estado_servicio', False) != 'baja':
                    service_vals['estado_servicio'] = 'baja'
                if 'fecha_baja' in service._fields and not getattr(service, 'fecha_baja', False):
                    service_vals['fecha_baja'] = fecha_baja
                if service_vals:
                    service.write(service_vals)
            if service:
                extra_changes = rec._build_service_changes(service_before, service)
            else:
                extra_changes = []
            rec._post_write_audit(before, extra_changes=extra_changes, title='Baja incobrable registrada')

    def action_marcar_recuperado(self):
        for rec in self:
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
            before = rec._get_audit_snapshot()
            rec.with_context(skip_incobrable_audit=True).write({'state': 'recuperado'})
            extra_changes = [
                ('Pago de recuperación', self._get_record_display_value(pago_pagado)),
                ('Períodos validados', ', '.join(periodos_adeudados)),
            ]
            rec._post_write_audit(before, extra_changes=extra_changes, title='Recuperación de incobrable registrada')

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

    def action_open_pagos_contrato(self):
        self.ensure_one()
        if not self.contract_id:
            raise ValidationError('No hay contrato asociado a este registro incobrable.')

        # Elevate privileges to access ir.ui.view
        self_sudo = self.sudo()

        action = {
            'type': 'ir.actions.act_window',
            'name': f'Pagos -- {self.contract_id.name or self.partner_id.name}',
            'res_model': 'wigo.pago.estado',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.contract_id.id)],
            'context': {'default_contract_id': self.contract_id.id},
            'target': 'current',
        }

        list_view = self_sudo.env.ref('wigo_cobranza.view_payment_state_list', raise_if_not_found=False)
        form_view = self_sudo.env.ref('wigo_cobranza.view_payment_state_form', raise_if_not_found=False)
        views = []
        if list_view:
            views.append((list_view.id, list_view.type or 'list'))
        if form_view:
            views.append((form_view.id, form_view.type or 'form'))
        if views:
            action['views'] = views
            action['view_mode'] = ','.join([t for _, t in views])
            return action

        View = self_sudo.env['ir.ui.view']
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
            for vid, vtype in ordered:
                if vtype == 'tree':
                    action['views'] = [(vid, 'tree')]
                    action['view_mode'] = 'tree'
                    return action
            action['views'] = ordered
        return action

    @api.model
    def create_from_overdue_payment(self, pago_estado):
        existing = self.search([
            ('partner_id', '=', pago_estado.partner_id.id),
            ('contract_id', '=', pago_estado.contract_id.id),
            ('state', '!=', 'recuperado'),
        ], limit=1)
        if existing:
            return existing

        return self.with_context(incobrable_audit_origin='Generación automática por mora').create({
            'partner_id': pago_estado.partner_id.id,
            'contract_id': pago_estado.contract_id.id,
            'client_service_id': pago_estado.client_service_id.id or False,
            'meses_adeudados': pago_estado.periodo,
            'monto_total_adeudado': pago_estado.monto_a_cobrar,
            'state': 'activo',
        })
