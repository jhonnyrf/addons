# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    post_sale_call_history_id = fields.Many2one(
        'crm.post.sale.call',
        string='Historial llamada posventa',
        copy=False,
    )

    is_post_sale_activity = fields.Boolean(
        string='Es actividad de posventa',
        compute='_compute_is_post_sale_activity',
        search='_search_is_post_sale_activity',
        store=False,
    )
    post_sale_client_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        compute='_compute_post_sale_client_fields',
        store=True,
        readonly=True,
    )
    post_sale_cf_code = fields.Char(
        string='Codigo CF',
        compute='_compute_post_sale_client_fields',
        store=True,
        readonly=True,
    )
    post_sale_contact_phone = fields.Char(
        string='Telefono de contacto',
        compute='_compute_post_sale_client_fields',
        store=True,
        readonly=True,
    )
    post_sale_is_active_customer = fields.Boolean(
        string='Cliente activo',
        compute='_compute_post_sale_client_fields',
        store=True,
        readonly=True,
    )
    post_sale_call_date = fields.Datetime(
        string='Fecha de llamada',
        default=lambda self: fields.Datetime.now(),
    )
    post_sale_done_by = fields.Many2one(
        'res.users',
        string='Realizada por',
        default=lambda self: self.env.user,
    )
    post_sale_satisfaction = fields.Selection(
        [
            ('satisfied', 'Satisfecho'),
            ('partial', 'Parcialmente satisfecho'),
            ('unsatisfied', 'Insatisfecho'),
        ],
        string='Nivel de satisfaccion',
    )
    post_sale_customer_comment = fields.Text(
        string='Comentarios del cliente',
    )
    post_sale_state = fields.Selection(
        [('pending', 'Pendiente'), ('done', 'Realizada')],
        string='Estado posventa',
        default='pending',
        required=True,
    )

    @api.depends('activity_type_id')
    def _compute_is_post_sale_activity(self):
        rel_model = self.env['crm.post.sale.activity.type']
        post_sale_type_ids = set(rel_model.search([]).mapped('activity_type_id').ids)
        for activity in self:
            activity.is_post_sale_activity = bool(activity.activity_type_id.id in post_sale_type_ids)

    def _search_is_post_sale_activity(self, operator, value):
        rel_model = self.env['crm.post.sale.activity.type']
        post_sale_type_ids = rel_model.search([]).mapped('activity_type_id').ids
        if operator in ('=', '=='):
            return [('activity_type_id', 'in' if value else 'not in', post_sale_type_ids)]
        if operator in ('!=', '<>'):
            return [('activity_type_id', 'not in' if value else 'in', post_sale_type_ids)]
        return [('id', '=', 0)]

    def _post_sale_summary_html(self):
        self.ensure_one()
        satisfaction_labels = dict(self._fields['post_sale_satisfaction'].selection)
        state_labels = dict(self._fields['post_sale_state'].selection)
        satisfaction_text = satisfaction_labels.get(self.post_sale_satisfaction, '-')
        state_text = state_labels.get(self.post_sale_state, '-')
        call_date = fields.Datetime.to_string(self.post_sale_call_date) if self.post_sale_call_date else '-'
        done_by = self.post_sale_done_by.name or '-'
        cf_code = self.post_sale_cf_code or '-'
        comment = self.post_sale_customer_comment or '-'

        return Markup(
            "<b>Seguimiento Posventa</b><br/>"
            f"Cliente: {self.post_sale_client_id.display_name or self.res_name or '-'}<br/>"
            f"Codigo CF: {cf_code}<br/>"
            f"Fecha de llamada: {call_date}<br/>"
            f"Realizada por: {done_by}<br/>"
            f"Estado: {state_text}<br/>"
            f"Nivel de satisfaccion: {satisfaction_text}<br/>"
            f"Comentarios: {comment}"
        )

    def _sync_post_sale_call_history(self):
        CallHistory = self.env['crm.post.sale.call']
        for activity in self.filtered('is_post_sale_activity'):
            lead = self.env['crm.lead'].browse(activity.res_id) if activity.res_model == 'crm.lead' and activity.res_id else False
            vals = {
                'activity_id': activity.id,
                'lead_id': lead.id if lead and lead.exists() else False,
                'post_sale_client_id': activity.post_sale_client_id.id,
                'post_sale_cf_code': activity.post_sale_cf_code or False,
                'post_sale_call_date': activity.post_sale_call_date or fields.Datetime.now(),
                'post_sale_done_by': activity.post_sale_done_by.id or self.env.user.id,
                'post_sale_satisfaction': activity.post_sale_satisfaction or False,
                'post_sale_customer_comment': activity.post_sale_customer_comment or False,
                'post_sale_state': activity.post_sale_state or 'pending',
            }

            history = activity.post_sale_call_history_id
            if history:
                history.write(vals)
            else:
                history = CallHistory.create(vals)
                activity.post_sale_call_history_id = history.id

    @api.depends('res_model', 'res_id')
    def _compute_post_sale_client_fields(self):
        Lead = self.env['crm.lead']
        for activity in self:
            activity.post_sale_client_id = False
            activity.post_sale_cf_code = False
            activity.post_sale_contact_phone = False
            activity.post_sale_is_active_customer = False
            if activity.res_model != 'crm.lead' or not activity.res_id:
                continue
            lead = Lead.browse(activity.res_id)
            if not lead.exists():
                continue
            activity.post_sale_client_id = lead.partner_id.id
            activity.post_sale_cf_code = lead.codigo_cliente or False
            partner = lead.partner_id
            phone = partner.phone if 'phone' in partner._fields else False
            mobile = partner.mobile if 'mobile' in partner._fields else False
            activity.post_sale_contact_phone = phone or mobile or False
            activity.post_sale_is_active_customer = bool(
                lead.contract_id and lead.contract_state in ('active', 'signed')
            )

    @api.onchange('activity_type_id')
    def _onchange_post_sale_defaults(self):
        for activity in self:
            if not activity.is_post_sale_activity:
                continue
            if not activity.post_sale_done_by:
                activity.post_sale_done_by = self.env.user
            if not activity.post_sale_call_date:
                activity.post_sale_call_date = fields.Datetime.now()
            if not activity.summary:
                activity.summary = 'Llamada de seguimiento postventa'

    def _is_lead_active_customer(self):
        self.ensure_one()
        if self.res_model != 'crm.lead' or not self.res_id:
            return False
        lead = self.env['crm.lead'].browse(self.res_id)
        return bool(lead.exists() and lead.contract_id and lead.contract_state in ('active', 'signed'))

    @api.constrains(
        'activity_type_id',
        'res_model',
        'res_id',
        'post_sale_call_date',
        'post_sale_done_by',
        'post_sale_state',
        'post_sale_satisfaction',
        'post_sale_customer_comment',
    )
    def _check_post_sale_requirements(self):
        for activity in self:
            if not activity.is_post_sale_activity:
                continue

            if activity.res_model != 'crm.lead':
                raise ValidationError(
                    _('Las actividades de posventa solo se pueden registrar en oportunidades/clientes del CRM.')
                )

            if not activity._is_lead_active_customer():
                raise ValidationError(
                    _('La llamada de posventa solo se puede registrar para clientes activos con contrato vigente.')
                )

            if not activity.post_sale_call_date:
                raise ValidationError(_('Debe indicar la fecha de llamada.'))

            if not activity.post_sale_done_by:
                raise ValidationError(_('Debe indicar quien realizo la llamada.'))

            if activity.post_sale_state == 'done' and not activity.post_sale_satisfaction:
                raise ValidationError(_('Debe registrar el nivel de satisfaccion cuando la llamada este realizada.'))

            if activity.post_sale_state == 'done' and not activity.post_sale_customer_comment:
                raise ValidationError(_('Debe registrar los comentarios del cliente cuando la llamada este realizada.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_post_sale_call_history()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_post_sale_call_history()
        return res

    def action_done(self):
        post_sale_activities = self.filtered('is_post_sale_activity')
        for activity in post_sale_activities:
            if not activity.post_sale_call_date:
                activity.post_sale_call_date = fields.Datetime.now()
            activity.post_sale_state = 'done'

        post_sale_activities._sync_post_sale_call_history()

        res = super().action_done()

        for activity in post_sale_activities:
            if activity.res_model != 'crm.lead' or not activity.res_id:
                continue
            lead = self.env['crm.lead'].browse(activity.res_id)
            if lead.exists():
                lead.message_post(body=activity._post_sale_summary_html())

        return res
