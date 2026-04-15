# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HelpdeskSlaAdvancedWizard(models.TransientModel):
    _name = 'helpdesk.sla.advanced.wizard'
    _description = 'Configuracion SLA del Ticket'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', required=True)

    # Info de solo lectura (actual)
    sla_status = fields.Selection(related='ticket_id.sla_status', string='Estado SLA', readonly=True)
    sla_deadline_current = fields.Datetime(
        string='Límite actual', compute='_compute_current_sla', readonly=True,
    )
    sla_hours_remaining_current = fields.Float(
        string='Horas restantes actuales', compute='_compute_current_sla', readonly=True,
    )
    sla_hours_remaining_current_display = fields.Char(
        string='Tiempo restante actual', compute='_compute_current_sla', readonly=True,
    )

    # Vista previa según selección del wizard
    sla_deadline_preview = fields.Datetime(
        string='Límite previsto', compute='_compute_sla_preview', readonly=True,
    )
    sla_hours_remaining_preview = fields.Float(
        string='Horas restantes previstas', compute='_compute_sla_preview', readonly=True,
    )
    sla_hours_remaining_preview_display = fields.Char(
        string='Tiempo restante previsto', compute='_compute_sla_preview', readonly=True,
    )

    # Modo de configuracion
    sla_mode = fields.Selection([
        ('quick', 'Dias'),
        ('advanced', 'Avanzado'),
    ], string='Modo', default='quick', required=True)

    # Modo rapido
    sla_quick_days = fields.Selection([
        ('1', '1 día'),
        ('2', '2 días'),
        ('3', '3 días'),
        ('4', '4 días'),
        ('5', '5 días'),
        ('6', '6 días'),
        ('7', '7 días'),
    ], string='Duración', default='2')

    # Modo avanzado
    sla_start_datetime = fields.Datetime(string='Inicio SLA')
    sla_end_datetime = fields.Datetime(string='Fin SLA')

    @staticmethod
    def _format_hours_display(hours_value):
        total_minutes = int(round(abs(hours_value or 0.0) * 60))
        hours, minutes = divmod(total_minutes, 60)
        if (hours_value or 0.0) < 0:
            return f'Vencido por {hours} h {minutes:02d} min'
        return f'{hours} h {minutes:02d} min'

    @api.depends('ticket_id', 'ticket_id.sla_deadline', 'ticket_id.is_closed', 'ticket_id.date_closed')
    def _compute_current_sla(self):
        now = fields.Datetime.now()
        for wizard in self:
            deadline = wizard.ticket_id.sla_deadline
            wizard.sla_deadline_current = deadline
            if deadline and not wizard.ticket_id.is_closed:
                wizard.sla_hours_remaining_current = (deadline - now).total_seconds() / 3600.0
                wizard.sla_hours_remaining_current_display = wizard._format_hours_display(wizard.sla_hours_remaining_current)
            else:
                wizard.sla_hours_remaining_current = 0.0
                wizard.sla_hours_remaining_current_display = '0 h 00 min'

    @api.depends('ticket_id', 'sla_mode', 'sla_quick_days', 'sla_start_datetime', 'sla_end_datetime')
    def _compute_sla_preview(self):
        now = fields.Datetime.now()
        for wizard in self:
            base = wizard.sla_start_datetime or wizard.ticket_id.date_open or wizard.ticket_id.create_date or now
            deadline = False

            if wizard.sla_mode == 'quick':
                base = now
                wizard.sla_start_datetime = base
                if wizard.sla_quick_days:
                    deadline = base + timedelta(days=int(wizard.sla_quick_days))
            else:
                deadline = wizard.sla_end_datetime or False

            wizard.sla_deadline_preview = deadline
            wizard.sla_hours_remaining_preview = (
                (deadline - now).total_seconds() / 3600.0 if deadline else 0.0
            )
            wizard.sla_hours_remaining_preview_display = (
                wizard._format_hours_display(wizard.sla_hours_remaining_preview) if deadline else '0 h 00 min'
            )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        ticket_id = self.env.context.get('default_ticket_id') or self.env.context.get('active_id')
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            mode = ticket.sla_mode or 'quick'
            vals.setdefault('ticket_id', ticket.id)
            vals.setdefault('sla_mode', mode)
            vals.setdefault('sla_quick_days', ticket.sla_quick_days or '2')
            if mode == 'quick':
                vals.setdefault('sla_start_datetime', fields.Datetime.now())
            else:
                vals.setdefault('sla_start_datetime', ticket.sla_start_datetime or ticket.date_open or fields.Datetime.now())
            vals.setdefault('sla_end_datetime', ticket.sla_end_datetime or ticket.sla_deadline or fields.Datetime.now())
        return vals

    def action_apply(self):
        self.ensure_one()
        ticket = self.ticket_id

        if self.sla_mode == 'quick':
            days = int(self.sla_quick_days or 2)
            base = fields.Datetime.now()
            deadline = base + timedelta(days=days)
            ticket.write({
                'sla_mode': 'quick',
                'sla_quick_days': self.sla_quick_days,
                'sla_deadline': deadline,
                'sla_end_datetime': deadline,
                'sla_start_datetime': base,
            })
        else:
            if not self.sla_start_datetime or not self.sla_end_datetime:
                raise ValidationError('Debes indicar la fecha de inicio y fin SLA.')
            if self.sla_end_datetime < self.sla_start_datetime:
                raise ValidationError('La fecha fin SLA no puede ser anterior al inicio.')
            ticket.write({
                'sla_mode': 'advanced',
                'sla_start_datetime': self.sla_start_datetime,
                'sla_end_datetime': self.sla_end_datetime,
                'sla_deadline': self.sla_end_datetime,
            })
        return {'type': 'ir.actions.act_window_close'}
