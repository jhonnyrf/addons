# -*- coding: utf-8 -*-
from datetime import timedelta
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Ticket de Helpdesk WigoFast'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc, id desc'
    _rec_name = 'title'

    # =========================================================================
    # IDENTIFICACIÓN
    # =========================================================================
    name = fields.Char(
        string='Número', readonly=True, copy=False, 
        default='/',
        index=True
    )
    name_display = fields.Char(
        string='Número', 
        compute='_compute_name_display',
        help='Muestra el número del ticket'
    )
    title = fields.Char(string='Título / Descripción breve', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True)

    # =========================================================================
    # CLIENTE — vinculación con res.partner (auto-llenado)
    # =========================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente (Odoo)',
        tracking=True,
        index=True,
        help='Selecciona el contacto de Odoo para auto-completar datos del cliente WigoFast.',
    )

    create_month = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes', compute='_compute_create_date_parts', store=True)

    create_year = fields.Selection([
        (str(y), str(y)) for y in range(2024, 2035)
    ], string='Año', compute='_compute_create_date_parts', store=True)

    resolution_time_hrs = fields.Float(
        string='Tiempo de Solución (hrs)', 
        compute='_compute_resolution_time', 
        store=True, 
        aggregator='avg',
        help='Tiempo en horas desde que se creó hasta que se cerró el ticket.'
    )

    @api.depends('create_date', 'date_closed')
    def _compute_resolution_time(self):
        for ticket in self:
            if ticket.create_date and ticket.date_closed:
                delta = ticket.date_closed - ticket.create_date
                ticket.resolution_time_hrs = delta.total_seconds() / 3600.0
            else:
                ticket.resolution_time_hrs = 0.0

    @api.depends('create_date')
    def _compute_create_date_parts(self):
        for ticket in self:
            if ticket.create_date:
                ticket.create_month = ticket.create_date.strftime('%m')
                ticket.create_year = ticket.create_date.strftime('%Y')
            else:
                ticket.create_month = False
                ticket.create_year = False

    contract_id = fields.Many2one(
        comodel_name='customer.contract',
        string='Contrato',
        domain="[('state', 'in', ['signed', 'active'])]",
        tracking=True,
        index=True,
        help='Selecciona un contrato activo o firmado. Se autocompletan los datos del cliente y plan.',
    )
    ftth_service_id = fields.Many2one(
        comodel_name='wigo.ftth.client.service',
        string='Ficha técnica',
        tracking=True,
        index=True,
        domain="[('partner_id', '=', partner_id)]",
        help='Este es el enlace para ver mas detalle tecnico del servicio del cliente.',
    )
    customer_code = fields.Char(string='Código Cliente', tracking=True, index=True)
    customer_name = fields.Char(string='Nombre completo', required=True, tracking=True)
    customer_ci = fields.Char(string='Cédula de Identidad (CI)', tracking=True)
    customer_phone = fields.Char(string='Celular', tracking=True)
    customer_phone_alt = fields.Char(string='Telefono', help='Telefono del cliente')
    customer_address = fields.Char(string='Dirección del Cliente', tracking=True)
    customer_zone = fields.Char(string='Zona', tracking=True, index=True)
    customer_plan_id = fields.Many2one(
        comodel_name='internet.plan',
        string='Plan Contratado',
        tracking=True,
    )
    customer_plan = fields.Selection(
        selection=[
            ('10', '10 Mbps'), ('20', '20 Mbps'), ('30', '30 Mbps'), ('50', '50 Mbps'),
            ('100', '100 Mbps'), ('200', '200 Mbps'), ('custom', 'Plan Personalizado'),
        ],
        string='Plan Contratado (legacy)', tracking=True,
    )
    onu_serial = fields.Char(string='Número de Serie ONU', tracking=True)
    olt_interface = fields.Char(string='Subinterfaz OLT', tracking=True, help='Ej: 1/1/5')
    customer_box = fields.Char(string='Caja / Splitter', tracking=True)
    nodo_id = fields.Many2one(
        comodel_name='wigo.ftth.nodo',
        string='Nodo',
        related='ftth_service_id.nodo_id',
        readonly=True,
    )
    olt_id = fields.Many2one(
        comodel_name='wigo.ftth.olt',
        string='OLT',
        related='ftth_service_id.olt_id',
        readonly=True,
    )
    olt_port_id = fields.Many2one(
        comodel_name='wigo.ftth.olt.port',
        string='Puerto OLT',
        related='ftth_service_id.olt_port_id',
        readonly=True,
    )
    subinterface_id = fields.Many2one(
        comodel_name='wigo.ftth.subinterface',
        string='Subinterfaz OLT',
        related='ftth_service_id.subinterface_id',
        readonly=True,
    )
    odn_id = fields.Many2one(
        comodel_name='wigo.ftth.odn',
        string='ODN',
        related='ftth_service_id.odn_id',
        readonly=True,
    )
    box_group_id = fields.Many2one(
        comodel_name='wigo.ftth.box.group',
        string='Grupo de cajas',
        related='ftth_service_id.box_group_id',
        readonly=True,
    )
    box_id = fields.Many2one(
        comodel_name='wigo.ftth.box',
        string='NAP',
        related='ftth_service_id.box_id',
        readonly=True,
    )
    box_port_id = fields.Many2one(
        comodel_name='wigo.ftth.box.port',
        string='Puerto NAP',
        related='ftth_service_id.box_port_id',
        readonly=True,
    )
    ruta_ftth = fields.Char(
        string='Ruta FTTH',
        related='ftth_service_id.ruta',
        readonly=True,
    )
    onu_id = fields.Many2one(
        comodel_name='wigo.ftth.onu',
        string='ONU / ONT',
        related='ftth_service_id.onu_id',
        readonly=True,
    )
    onu_marca = fields.Char(
        string='Marca ONU',
        related='onu_id.marca',
        readonly=True,
    )
    onu_modelo = fields.Char(
        string='Modelo ONU',
        related='onu_id.modelo',
        readonly=True,
    )
    pon_sn = fields.Char(
        string='PON S/N',
        related='onu_id.pon_sn',
        readonly=True,
    )
    is_recurrent_customer = fields.Boolean(
        string='Cliente Recurrente',
        compute='_compute_is_recurrent_customer',
        search='_search_is_recurrent_customer',
        store=False,
    )

    # =========================================================================
    # CLASIFICACIÓN DEL TICKET
    # =========================================================================
    stage_id = fields.Many2one(
        comodel_name='helpdesk.stage', string='Etapa', ondelete='restrict',
        tracking=True, group_expand='_read_group_stage_ids', copy=False, index=True,
    )
    ticket_type = fields.Selection(
        selection=[
            ('incident', 'Reclamo / Incidente'),
            ('request', 'Solicitud'),
        ],
        string='Tipo de Ticket (legacy)',
        default='incident',
        tracking=True,
        index=True,
        help='DEPRECATED: usar ticket_type_id en su lugar',
    )
    ticket_type_id = fields.Many2one(
        comodel_name='helpdesk.ticket.type',
        string='Tipo de Ticket',
        tracking=True,
        index=True,
        help='Seleccione el tipo de ticket para clasificar correctamente la atencion.',
        default=lambda self: self.env['helpdesk.ticket.type'].search([], order='sequence', limit=1),
    )
    category_id = fields.Many2one(
        comodel_name='helpdesk.category', string='Categoría', tracking=True, index=True,
    )
    incident_type_id = fields.Many2one(
        comodel_name='helpdesk.incident.type',
        string='Sintoma',
        tracking=True,
        index=True,
        help='Seleccione sintoma/incidencia y complete la informacion relacionada para guiar la atencion.',
    )
    symptom_priority = fields.Many2one(
        related='incident_type_id.priority_suggestion',
        string='Prioridad',
        readonly=True,
    )
    # Kept for backward compat / search
    incident_type = fields.Char(
        string='Tipo (legacy)',
        related='incident_type_id.code',
        store=True,
        index=True,
    )
    priority = fields.Selection(
        selection=[('0', 'Baja'), ('1', 'Media'), ('2', 'Alta'), ('3', 'Crítica')],
        string='Prioridad', default='1', tracking=True, index=True,
    )
    priority_dirty = fields.Boolean(
        string='Prioridad modificada',
        compute='_compute_priority_dirty',
        store=True,
        help='Detecta si el usuario cambió la prioridad después de creado el ticket',
    )
    tag_ids = fields.Many2many(
        comodel_name='helpdesk.tag', relation='helpdesk_ticket_tag_rel',
        column1='ticket_id', column2='tag_id', string='Etiquetas',
    )
    color = fields.Integer(string='Color', default=0, aggregator=False)


    # =========================================================================
    # CANAL DE ORIGEN
    # =========================================================================
    channel = fields.Selection(
        selection=[
            ('whatsapp', 'WhatsApp'), ('call', 'Llamada telefónica'), ('visit', 'Visita presencial'),
            ('promoter', 'Promotor en campo'), ('web', 'Formulario web'),
            ('internal', 'Interno'), ('other', 'Otro'),
        ],
        string='Canal de Origen', default='whatsapp', tracking=True, index=True, required=True,
    )

    # =========================================================================
    # ASIGNACIÓN
    # =========================================================================
    team_id = fields.Many2one(comodel_name='helpdesk.team', string='Área', index=True)
    area_id = fields.Many2one(
        comodel_name='hr.department',
        string='Área',
        index=True,
        help='Selecciona el departamento o área responsable del ticket.',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Asignado a',
        index=True,
        domain="[('department_id', 'child_of', area_id)]",
        help='Solo muestra empleados del área seleccionada.',
    )
    user_id = fields.Many2one(
        comodel_name='res.users', string='Asignado a', index=True,
        domain="[('share', '=', False)]",
    )
    escalated_to_id = fields.Many2one(
        comodel_name='res.users', string='Escalado a', domain="[('share', '=', False)]",
    )
    escalated_team_id = fields.Many2one(comodel_name='helpdesk.team', string='Área escalada')
    is_escalated = fields.Boolean(string='Escalado', default=False, index=True)
    escalation_reason = fields.Text(string='Motivo de Escalamiento')

    # =========================================================================
    # DESCRIPCIÓN Y RESOLUCIÓN
    # =========================================================================
    description = fields.Html(string='Descripción del Problema')
    resolution_notes = fields.Html(string='Notas de Resolución')
    technical_notes = fields.Text(string='Notas Técnicas Internas')
    knowledge_id = fields.Many2one(comodel_name='helpdesk.knowledge', string='Artículo KB relacionado')
    # Diagnóstico y Solución movidos a Resolución (antes en Visita Técnica)
    resolution_diagnosis_id = fields.Many2one(
        comodel_name='helpdesk.visit.diagnosis.type',
        string='Diagnóstico',
        tracking=True,
        help='Diagnóstico principal del problema resuelto.',
    )
    resolution_solution_id = fields.Many2one(
        comodel_name='helpdesk.visit.solution.type',
        string='Solución Aplicada',
        tracking=True,
        help='Tipo de solución aplicada para resolver el ticket.',
    )
    resolution_diagnosis_detail = fields.Text(
        string='Detalle de Diagnóstico',
        tracking=True,
    )
    resolution_solution_detail = fields.Text(
        string='Detalle de Solución',
        tracking=True,
    )

    # =========================================================================
    # VISITA TÉCNICA
    # =========================================================================
    requires_visit = fields.Boolean(string='Requiere visita técnica', default=False, tracking=True)
    technician_id = fields.Many2one(
        'hr.employee',
        string='Técnico asignado',
        compute='_compute_latest_visit',
        inverse='_inverse_latest_visit',
        store=True,
    )
    visit_date = fields.Datetime(
        string='Fecha programada',
        compute='_compute_latest_visit',
        inverse='_inverse_latest_visit',
        store=True,
        default=fields.Datetime.now,
    )
    visit_result = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('in_progress', 'En progreso'),
            ('done', 'Realizada'),
            ('rescheduled', 'Reagendada'),
            ('cancelled', 'Cancelada')
        ],
        string='Estado de la visita',
        compute='_compute_latest_visit',
        inverse='_inverse_latest_visit',
        store=True,
    )
    visit_ids = fields.One2many(
        'helpdesk.visit',
        'ticket_id',
        string='Historial de Visitas'
    )
    visit_deadline = fields.Date(
        string='Fecha límite de la visita',
        compute='_compute_latest_visit',
        inverse='_inverse_latest_visit',
        store=True,
    )
    visit_notes = fields.Text(
        string='Notas de la visita',
        compute='_compute_latest_visit',
        inverse='_inverse_latest_visit',
        store=True,
    )
    visit_diagnosis_id = fields.Many2one(
        comodel_name='helpdesk.visit.diagnosis.type',
        string='Diagnostico principal',
        tracking=True,
    )
    visit_solution_id = fields.Many2one(
        comodel_name='helpdesk.visit.solution.type',
        string='Solucion aplicada',
        tracking=True,
    )
    visit_diagnosis = fields.Text(string='Diagnostico de visita', tracking=True)
    visit_solution = fields.Text(string='Solucion aplicada', tracking=True)
    visit_solution_detail = fields.Html(string='Detalle de solucion')

    # =========================================================================
    # FECHAS Y SLA
    # =========================================================================
    date_open = fields.Datetime(string='Fecha de Apertura', copy=False, tracking=True)
    date_closed = fields.Datetime(string='Fecha de Cierre', readonly=True, copy=False, tracking=True)
    sla_mode = fields.Selection(
        selection=[
            ('quick', 'Simple (dias)'),
            ('advanced', 'Avanzado (fecha y hora)'),
        ],
        string='Modo SLA',
        default='advanced',
        tracking=True,
    )
    sla_start_datetime = fields.Datetime(
        string='Inicio SLA',
        tracking=True,
        default=fields.Datetime.now,
    )
    sla_end_datetime = fields.Datetime(
        string='Fin SLA',
        tracking=True,
        help='En modo avanzado, este valor define la fecha limite SLA.',
    )
    sla_quick_days = fields.Selection(
        selection=[
            ('1', '1 dia'),
            ('2', '2 dias'),
            ('3', '3 dias'),
            ('4', '4 dias'),
            ('5', '5 dias'),
            ('6', '6 dias'),
            ('7', '7 dias'),
        ],
        string='SLA rapido',
        default=lambda self: str(self.env['helpdesk.sla.config'].get_default_ticket_sla_days()),
        tracking=True,
        help='Selecciona dias predefinidos. Tambien puedes editar la fecha limite manualmente.',
    )
    sla_deadline = fields.Datetime(string='Fecha Límite SLA', tracking=True,
        help='Calculado automáticamente según prioridad/categoría. Puedes modificarlo manualmente.')
    sla_exceeded = fields.Boolean(string='SLA Excedido', compute='_compute_sla_exceeded', store=True)
    # Semáforo: ok=verde, warning=amarillo, danger=rojo, closed=gris
    sla_status = fields.Selection(
        selection=[
            ('ok', 'En tiempo'), ('warning', 'Próximo a vencer'),
            ('danger', 'Vencido'), ('closed', 'Cerrado'),
        ],
        string='Estado SLA', compute='_compute_sla_status', store=False,
        search='_search_sla_status',
    )
    sla_hours_remaining = fields.Float(
        string='Horas restantes SLA', compute='_compute_sla_hours_remaining', store=False,
    )
    sla_hours_remaining_display = fields.Char(
        string='Tiempo restante SLA', compute='_compute_sla_hours_remaining_display', store=False,
    )
    # Etiqueta del semáforo según config — usada en Kanban para texto dinámico
    sla_badge_label = fields.Char(
        string='Etiqueta SLA', compute='_compute_sla_badge', store=False,
    )
    sla_badge_icon = fields.Char(
        string='Ícono SLA', compute='_compute_sla_badge', store=False,
    )
    sla_badge_color = fields.Char(
        string='Color SLA', compute='_compute_sla_badge', store=False,
    )
    sla_progress_pct = fields.Float(
        string='Progreso SLA (%)', compute='_compute_sla_progress_pct', store=False,
        help='Porcentaje de tiempo transcurrido del SLA total (0-100%). Se recalcula en cada lectura.',
    )
    # Estado SLA ya notificado por cron para evitar repetir mensajes
    sla_last_notified_status = fields.Selection(
        selection=[
            ('ok', 'En tiempo'),
            ('warning', 'Próximo a vencer'),
            ('danger', 'Vencido'),
            ('closed', 'Cerrado'),
        ],
        string='Último estado SLA notificado',
        copy=False,
        tracking=False,
        index=True,
    )
    sla_last_notified_at = fields.Datetime(
        string='Última notificación SLA',
        copy=False,
        tracking=False,
    )

    # =========================================================================
    # POSTVENTA / SATISFACCIÓN
    # =========================================================================
    postventa_done = fields.Boolean(string='Llamada postventa realizada', default=False, tracking=True)
    postventa_date = fields.Date(string='Fecha de llamada postventa', tracking=True)
    postventa_user_id = fields.Many2one(
        comodel_name='res.users', string='Realizado por', domain="[('share', '=', False)]",
    )
    postventa_activity_id = fields.Many2one(
        comodel_name='mail.activity',
        string='Actividad de postventa',
        readonly=True,
        copy=False,
    )
    satisfaction = fields.Selection(
        selection=[
            ('1', '⭐ Muy insatisfecho'), ('2', '⭐⭐ Insatisfecho'), ('3', '⭐⭐⭐ Neutral'),
            ('4', '⭐⭐⭐⭐ Satisfecho'), ('5', '⭐⭐⭐⭐⭐ Muy satisfecho'),
        ],
        string='Nivel de Satisfacción', tracking=True,
    )
    postventa_notes = fields.Text(string='Observaciones postventa')
    postventa_call_ids = fields.One2many(
        'helpdesk.postventa.call', 
        'ticket_id', 
        string='Llamadas de Seguimiento Postventa'
    )

    # =========================================================================
    # ESTADO CALCULADO
    # =========================================================================
    is_closed = fields.Boolean(string='Cerrado', related='stage_id.is_close', store=True, index=True)

    # =========================================================================
    # COMPUTES
    # =========================================================================
    @api.onchange('sla_mode', 'sla_quick_days', 'sla_start_datetime', 'sla_end_datetime', 'category_id')
    def _onchange_sla_deadline(self):
        """Sugiere fecha límite SLA automáticamente usando prioridades SLA.
        NOTA: incident_type_id se maneja exclusivamente en _onchange_incident_type
        para garantizar que el cambio de síntoma SIEMPRE recalcule el SLA.
        Las estrellas (priority) son selección manual y NO recalculan el SLA.
        """
        cfg = self.env['helpdesk.sla.config'].get_config()
        
        priority_hours = {}
        for p in cfg.priority_sla_ids:
            if p.sequence == 50:
                priority_hours['3'] = p.hours_limit
            elif p.sequence == 20:
                priority_hours['2'] = p.hours_limit
            elif p.sequence == 30:
                priority_hours['1'] = p.hours_limit
            elif p.sequence == 40:
                priority_hours['0'] = p.hours_limit
        
        sla_by_priority = priority_hours
        
        for ticket in self:
            now_dt = fields.Datetime.now()
            base = ticket.sla_start_datetime or ticket.date_open or ticket.create_date or now_dt

            if ticket.sla_mode == 'advanced':
                # Si ya hay sla_deadline guardado, no sobreescribir desde este onchange
                # (el síntoma tiene su propio onchange que sí recalcula)
                if ticket.sla_deadline:
                    if not ticket.sla_end_datetime:
                        ticket.sla_end_datetime = ticket.sla_deadline
                    continue
                
                # Si hay sla_end_datetime establecido, usarlo
                if ticket.sla_end_datetime:
                    ticket.sla_deadline = ticket.sla_end_datetime
                # Si no hay nada, y hay síntoma, calcular desde horas del síntoma
                elif ticket.incident_type_id and ticket.incident_type_id.priority_suggestion and ticket.incident_type_id.priority_suggestion.hours_limit:
                    hours = ticket.incident_type_id.priority_suggestion.hours_limit
                    ticket.sla_end_datetime = base + timedelta(hours=hours)
                    ticket.sla_deadline = ticket.sla_end_datetime
                continue

            # Modo rapido por dias (1-7) tiene prioridad para facilitar carga operativa
            if ticket.sla_quick_days:
                # Mantener la fecha de inicio guardada; si no existe, usar apertura del ticket.
                ticket.sla_start_datetime = base
                ticket.sla_deadline = base + timedelta(days=int(ticket.sla_quick_days))
                ticket.sla_end_datetime = ticket.sla_deadline
                continue

            if ticket.sla_deadline:
                continue  # Ya tiene valor manual, no sobreescribir
            if ticket.category_id and ticket.category_id.sla_hours > 0:
                hours = ticket.category_id.sla_hours
            elif ticket.incident_type_id and ticket.incident_type_id.priority_suggestion and ticket.incident_type_id.priority_suggestion.hours_limit:
                hours = ticket.incident_type_id.priority_suggestion.hours_limit
            else:
                hours = sla_by_priority.get('1', 72.0)
            ticket.sla_deadline = base + timedelta(hours=hours)
            ticket.sla_end_datetime = ticket.sla_deadline

    @api.onchange('sla_mode')
    def _onchange_sla_mode_defaults(self):
        for ticket in self:
            if ticket.sla_mode == 'advanced':
                if not ticket.sla_start_datetime:
                    ticket.sla_start_datetime = ticket.date_open or fields.Datetime.now()
                if not ticket.sla_end_datetime and ticket.sla_deadline:
                    ticket.sla_end_datetime = ticket.sla_deadline
            else:
                if not ticket.sla_start_datetime:
                    ticket.sla_start_datetime = ticket.date_open or ticket.create_date or fields.Datetime.now()
                if not ticket.sla_quick_days:
                    ticket.sla_quick_days = str(self.env['helpdesk.sla.config'].get_default_ticket_sla_days())

    @api.onchange('sla_deadline')
    def _onchange_sla_deadline_manual(self):
        for ticket in self:
            if ticket.sla_deadline and ticket.sla_mode == 'advanced':
                ticket.sla_end_datetime = ticket.sla_deadline

    @api.constrains('sla_mode', 'sla_start_datetime', 'sla_end_datetime')
    def _check_sla_advanced_dates(self):
        for ticket in self:
            if ticket.sla_mode == 'advanced' and ticket.sla_start_datetime and ticket.sla_end_datetime:
                if ticket.sla_end_datetime < ticket.sla_start_datetime:
                    raise ValidationError('La fecha/hora fin SLA no puede ser anterior al inicio SLA.')

    @api.model_create_multi
    def _set_sla_on_create(self, vals_list):
        """Calcula SLA al crear si no fue especificado manualmente."""
        pass  # Handled in create override below

    @api.depends('sla_deadline', 'is_closed', 'date_closed')
    def _compute_sla_exceeded(self):
        now = fields.Datetime.now()
        for ticket in self:
            if not ticket.sla_deadline:
                ticket.sla_exceeded = False
            elif ticket.is_closed and ticket.date_closed:
                ticket.sla_exceeded = ticket.date_closed > ticket.sla_deadline
            else:
                ticket.sla_exceeded = now > ticket.sla_deadline

    @api.depends('sla_deadline', 'is_closed', 'date_closed', 'sla_start_datetime', 'date_open', 'create_date')
    def _compute_sla_status(self):
        """
        Semáforo SLA dinámico — lee umbrales desde helpdesk.sla.config.
        - closed : ticket cerrado (gris)
        - ok     : tiempo restante por encima de los umbrales (verde)
        - warning: tiempo restante dentro del umbral de aviso (amarillo)
        - danger : SLA vencido (rojo)
        """
        now = fields.Datetime.now()
        # Leer config una sola vez para todo el batch
        cfg = self.env['helpdesk.sla.config'].get_config()
        warn_pct = (cfg.warning_threshold_pct or 25.0) / 100.0
        warn_abs = cfg.warning_threshold_hours or 0.0

        for ticket in self:
            if ticket.is_closed:
                ticket.sla_status = 'closed'
                continue
            if not ticket.sla_deadline:
                ticket.sla_status = 'ok'
                continue
            start_dt = ticket.sla_start_datetime or ticket.date_open or ticket.create_date or now
            total_hours = (ticket.sla_deadline - start_dt).total_seconds() / 3600.0
            remaining = (ticket.sla_deadline - now).total_seconds() / 3600.0
            if remaining < 0:
                ticket.sla_status = 'danger'
            else:
                # Entra en amarillo si cumple cualquiera de los dos criterios configurados
                in_warning_pct = total_hours > 0 and (remaining / total_hours) < warn_pct
                in_warning_abs = warn_abs > 0 and remaining < warn_abs
                ticket.sla_status = 'warning' if (in_warning_pct or in_warning_abs) else 'ok'

    def _search_sla_status(self, operator, value):
        """Método de búsqueda para sla_status (store=False).
        Convierte el filtro de SLA en un dominio SQL basado en fechas.
        """
        now = fields.Datetime.now()
        cfg = self.env['helpdesk.sla.config'].get_config()
        warn_pct = (cfg.warning_threshold_pct or 25.0) / 100.0
        warn_abs_h = cfg.warning_threshold_hours or 0.0

        if operator not in ('=', '!=', 'in', 'not in'):
            return []

        values = [value] if isinstance(value, str) else list(value)

        def _domain_for_status(v):
            if v == 'closed':
                return [('is_closed', '=', True)]
            if v == 'danger':
                return [
                    ('is_closed', '=', False),
                    ('sla_deadline', '!=', False),
                    ('sla_deadline', '<', now),
                ]
            if v == 'warning':
                # Tickets abiertos, no vencidos, pero dentro de umbral
                # Umbral absoluto: quedan menos de warn_abs_h horas
                base = [('is_closed', '=', False), ('sla_deadline', '>=', now), ('sla_deadline', '!=', False)]
                if warn_abs_h > 0:
                    warn_dt = now + __import__('datetime').timedelta(hours=warn_abs_h)
                    base.append(('sla_deadline', '<=', warn_dt))
                return base
            if v == 'ok':
                # No vencido y no en warning (aproximación conservadora)
                domain = [('is_closed', '=', False), ('sla_deadline', '>=', now)]
                if warn_abs_h > 0:
                    warn_dt = now + __import__('datetime').timedelta(hours=warn_abs_h)
                    domain.append(('sla_deadline', '>', warn_dt))
                domain_no_deadline = [('sla_deadline', '=', False), ('is_closed', '=', False)]
                return ['|'] + domain + domain_no_deadline
            return [('id', '=', False)]

        domains = [_domain_for_status(v) for v in values]
        if not domains:
            return [('id', '=', False)]

        # Combinar con OR si hay múltiples valores
        result = domains[0]
        for extra in domains[1:]:
            result = ['|'] + result + extra

        if operator in ('!=', 'not in'):
            return ['!'] + result
        return result

    @api.depends('visit_ids', 'visit_ids.visit_date', 'visit_ids.deadline_date', 'visit_ids.technician_id', 'visit_ids.state', 'visit_ids.notes')
    def _compute_latest_visit(self):
        for ticket in self:
            if ticket.visit_ids:
                latest_visit = ticket.visit_ids[0]
                ticket.technician_id = latest_visit.technician_id.id
                ticket.visit_date = latest_visit.visit_date
                ticket.visit_deadline = latest_visit.deadline_date
                ticket.visit_result = latest_visit.state
                ticket.visit_notes = latest_visit.notes
            else:
                ticket.technician_id = False
                ticket.visit_date = False
                ticket.visit_deadline = False
                ticket.visit_result = 'pending'
                ticket.visit_notes = False

    def _inverse_latest_visit(self):
        for ticket in self:
            if not ticket.requires_visit:
                continue
                
            vals = {
                'technician_id': ticket.technician_id.id if ticket.technician_id else False,
                'visit_date': ticket.visit_date,
                'deadline_date': ticket.visit_deadline,
                'state': ticket.visit_result or 'pending',
                'notes': ticket.visit_notes,
            }
            
            if ticket.visit_ids:
                ticket.visit_ids[0].write(vals)
            else:
                vals['ticket_id'] = ticket.id
                self.env['helpdesk.visit'].create(vals)

    @api.depends('sla_deadline', 'is_closed')
    def _compute_sla_hours_remaining(self):
        now = fields.Datetime.now()
        for ticket in self:
            if ticket.is_closed or not ticket.sla_deadline:
                ticket.sla_hours_remaining = 0.0
                continue
            ticket.sla_hours_remaining = (ticket.sla_deadline - now).total_seconds() / 3600.0

    @api.depends('sla_status')
    def _compute_sla_badge(self):
        """Lee etiquetas/íconos de helpdesk.sla.config para el semáforo visual."""
        cfg = self.env['helpdesk.sla.config'].get_config()
        mapping = {
            'ok':      (cfg.ok_label or 'En tiempo',        cfg.ok_icon or 'fa-check-circle',        cfg.ok_color or '#28a745'),
            'warning': (cfg.warning_label or 'Próx. vencer', cfg.warning_icon or 'fa-clock-o',        cfg.warning_color or '#ffc107'),
            'danger':  (cfg.danger_label or 'SLA Vencido',   cfg.danger_icon or 'fa-exclamation-circle', cfg.danger_color or '#dc3545'),
            'closed':  (cfg.closed_label or 'Cerrado',       cfg.closed_icon or 'fa-check',           cfg.closed_color or '#6c757d'),
        }
        for ticket in self:
            label, icon, color = mapping.get(ticket.sla_status or 'ok', mapping['ok'])
            ticket.sla_badge_label = label
            ticket.sla_badge_icon = icon
            ticket.sla_badge_color = color

    @api.depends('sla_hours_remaining', 'sla_deadline', 'is_closed')
    def _compute_sla_hours_remaining_display(self):
        for ticket in self:
            if not ticket.sla_deadline or ticket.is_closed:
                ticket.sla_hours_remaining_display = '0 h 00 min'
                continue

            total_minutes = int(round(abs(ticket.sla_hours_remaining or 0.0) * 60))
            hours, minutes = divmod(total_minutes, 60)
            if (ticket.sla_hours_remaining or 0.0) < 0:
                ticket.sla_hours_remaining_display = f'Vencido por {hours} h {minutes:02d} min'
            else:
                ticket.sla_hours_remaining_display = f'{hours} h {minutes:02d} min'

    @api.depends('sla_deadline', 'sla_start_datetime', 'is_closed')
    def _compute_sla_progress_pct(self):
        """Calcula el porcentaje de tiempo usado del SLA."""
        for ticket in self:
            if not ticket.sla_deadline or not ticket.sla_start_datetime:
                ticket.sla_progress_pct = 0.0
                continue
            
            if ticket.is_closed:
                ticket.sla_progress_pct = 100.0
                continue
            
            total_seconds = (ticket.sla_deadline - ticket.sla_start_datetime).total_seconds()
            if total_seconds <= 0:
                ticket.sla_progress_pct = 100.0
                continue
            
            now = fields.Datetime.now()
            elapsed_seconds = max(0, (now - ticket.sla_start_datetime).total_seconds())
            progress = min(100.0, (elapsed_seconds / total_seconds) * 100.0)
            ticket.sla_progress_pct = progress

    @api.model
    def default_get(self, fields_list):
        """No genera el número aquí para evitar que avance la secuencia sin guardar."""
        res = super().default_get(fields_list)
        if 'name' in fields_list:
            res['name'] = '/'
        return res

    @api.depends('name')
    def _compute_name_display(self):
        for ticket in self:
            if ticket.id:
                ticket.name_display = ticket.name or '/'
            else:
                ticket.name_display = ''

    @api.depends('name', 'title')
    def _compute_display_name(self):
        for rec in self:
            if rec.name and rec.name != '/':
                rec.display_name = f'[{rec.name}] {rec.title}'
            else:
                rec.display_name = rec.title or '/'

    @api.depends('partner_id', 'contract_id', 'contract_id.partner_id', 'customer_code')
    def _compute_is_recurrent_customer(self):
        recurrent_ticket_ids = self._get_recurrent_ticket_ids()

        for ticket in self:
            ticket.is_recurrent_customer = ticket.id in recurrent_ticket_ids

    @api.depends('priority', 'create_date')
    def _compute_priority_dirty(self):
        for ticket in self:
            if not ticket.create_date:
                ticket.priority_dirty = False
                continue
            ticket.priority_dirty = True

    @api.model
    def _get_recurrent_customer_keys(self):
        """
        Cuenta tickets por clave de cliente. Un cliente es recurrente si
        aparece en más de un ticket. Se usan tres claves de identificación
        (con prioridad):
          1. partner comercial (partner_id o contract_id.partner_id)
          2. contract_id  (dos tickets del mismo contrato = recurrente)
          3. customer_code
        """
        partner_counts = {}
        contract_counts = {}
        code_counts = {}

        tickets = self.search([])

        for ticket in tickets:
            # Clave 1: partner comercial
            partner = (
                ticket.partner_id.commercial_partner_id
                or (ticket.contract_id and ticket.contract_id.partner_id
                    and ticket.contract_id.partner_id.commercial_partner_id)
            )
            if partner and partner.id:
                partner_counts[partner.id] = partner_counts.get(partner.id, 0) + 1

            # Clave 2: contrato (dos tickets del mismo contrato = recurrente)
            if ticket.contract_id and ticket.contract_id.id:
                contract_counts[ticket.contract_id.id] = contract_counts.get(ticket.contract_id.id, 0) + 1

            # Clave 3: código de cliente manual
            if ticket.customer_code:
                code_counts[ticket.customer_code] = code_counts.get(ticket.customer_code, 0) + 1

        recurrent_partner_ids = {pid for pid, count in partner_counts.items() if count > 1}
        recurrent_contract_ids = {cid for cid, count in contract_counts.items() if count > 1}
        recurrent_codes = {code for code, count in code_counts.items() if count > 1}
        return recurrent_partner_ids, recurrent_contract_ids, recurrent_codes

    @api.model
    def _get_recurrent_ticket_ids(self):
        recurrent_partner_ids, recurrent_contract_ids, recurrent_codes = self._get_recurrent_customer_keys()

        recurrent_ids = set()
        tickets = self.search([])
        for ticket in tickets:
            # Clave 1: partner comercial
            partner = (
                ticket.partner_id.commercial_partner_id
                or (ticket.contract_id and ticket.contract_id.partner_id
                    and ticket.contract_id.partner_id.commercial_partner_id)
            )
            partner_ref = partner.id if partner and partner.id else None

            # Clave 2: contrato
            contract_ref = ticket.contract_id.id if ticket.contract_id else None

            if (
                (partner_ref and partner_ref in recurrent_partner_ids)
                or (contract_ref and contract_ref in recurrent_contract_ids)
                or (ticket.customer_code and ticket.customer_code in recurrent_codes)
            ):
                recurrent_ids.add(ticket.id)
        return recurrent_ids

    @api.model
    def _search_is_recurrent_customer(self, operator, value):
        if operator not in ('=', '!='):
            return [('id', '=', 0)]

        recurrent_ids = list(self._get_recurrent_ticket_ids())

        target_true = (operator == '=' and bool(value)) or (operator == '!=' and not bool(value))
        if target_true:
            return [('id', 'in', recurrent_ids or [0])]

        return [('id', 'not in', recurrent_ids or [0])]

    # =========================================================================
    # ONCHANGE — Auto-llenado desde partner_id
    # =========================================================================
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        """Al seleccionar contrato, auto-completa datos del cliente y plan."""
        if not self.contract_id:
            return

        contract = self.contract_id
        partner = contract.partner_id
        lead = contract.lead_id
        if not lead:
            lead = self.env['crm.lead'].search([
                ('contract_id', '=', contract.id)
            ], order='id desc', limit=1)

        self.partner_id = partner.id
        self.customer_code = contract.name or partner.ref or ''
        self.customer_name = partner.name or ''
        self.customer_ci = getattr(partner, 'ci', False) or contract.ci or ''

        main_phone = contract.mobile or getattr(partner, 'celular', False) or getattr(partner, 'mobile', False) or partner.phone or ''
        alt_phone = partner.phone or getattr(partner, 'mobile', False) or ''
        if alt_phone == main_phone:
            alt_phone = ''

        self.customer_phone = main_phone
        self.customer_phone_alt = alt_phone
        self.customer_address = contract.address or partner.street or ''
        self.customer_zone = getattr(lead, 'zona', False) or contract.address or partner.city or ''
        self.customer_plan_id = contract.plan_id.id
        self._sync_ftth_service_from_partner(
            partner=partner,
            contract=contract,
            customer_code=self.customer_code,
        )

        # Compatibilidad con el campo legado selection
        speed = getattr(contract, 'plan_speed', False)
        self.customer_plan = str(speed) if speed and str(speed) in {'10', '20', '30', '50', '100', '200'} else 'custom'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Al seleccionar un contacto Odoo, auto-completa datos del cliente."""
        if self.contract_id:
            return
        if self.partner_id:
            p = self.partner_id
            if not self.customer_name:
                self.customer_name = p.name or ''
            # Teléfono titular
            if not self.customer_phone:
                self.customer_phone = p.phone or getattr(p, "mobile", None) or ""
            # Teléfono alternativo (si hay ambos)
            if not self.customer_phone_alt and p.phone and getattr(p, "mobile", None):
                self.customer_phone_alt = getattr(p, "mobile", None) or ""
            # Dirección
            if not self.customer_address:
                parts = [x for x in [p.street, p.street2, p.city] if x]
                self.customer_address = ', '.join(parts)
            # Código CF desde referencia interna del partner
            if not self.customer_code and p.ref:
                self.customer_code = p.ref
            self._sync_ftth_service_from_partner(
                partner=p,
                contract=False,
                customer_code=self.customer_code,
            )

    def _get_ftth_service_for_customer(self, partner=False, contract=False, customer_code=False):
        """Encuentra la ficha FTTH priorizando contrato/codigo y luego partner."""
        service_model = self.env['wigo.ftth.client.service']

        # 1) Prioridad alta: servicio vinculado a un lead del mismo contrato
        if contract:
            by_contract = service_model.search([
                ('lead_id.contract_id', '=', contract.id),
            ], order='fecha_instalacion desc, id desc', limit=1)
            if by_contract:
                return by_contract

        # 2) Prioridad media: coincidencia por codigo CF (contrato/codigo cliente)
        code_candidates = []
        if customer_code:
            code_candidates.append(customer_code)
        if contract and contract.name and contract.name not in code_candidates:
            code_candidates.append(contract.name)
        if partner and partner.ref and partner.ref not in code_candidates:
            code_candidates.append(partner.ref)

        for code in code_candidates:
            domain = [('codigo_cliente', '=', code)]
            if partner:
                domain = [('codigo_cliente', '=', code), ('partner_id', '=', partner.id)]
            by_code = service_model.search(domain, order='fecha_instalacion desc, id desc', limit=1)
            if by_code:
                return by_code

        # 3) Fallback: ultimo servicio del partner
        if partner:
            return service_model.search([
                ('partner_id', '=', partner.id),
            ], order='fecha_instalacion desc, id desc', limit=1)

        return service_model.browse()

    def _sync_ftth_service_from_partner(self, partner=False, contract=False, customer_code=False):
        service = self._get_ftth_service_for_customer(
            partner=partner,
            contract=contract,
            customer_code=customer_code,
        )
        if service:
            self.ftth_service_id = service
            self._onchange_ftth_service_id()
        else:
            self.ftth_service_id = False
            self.onu_serial = False
            self.olt_interface = False
            self.customer_box = False

    def _get_subinterface_code(self, subinterface):
        """Return the best available code/identifier for a FTTH subinterface."""
        if not subinterface:
            return ''
        return (
            getattr(subinterface, 'code', False)
            or getattr(subinterface, 'codigo', False)
            or subinterface.display_name
            or ''
        )

    def _get_box_identifier(self, box):
        """Return the best available identifier for a FTTH NAP box."""
        if not box:
            return ''
        return (
            getattr(box, 'identifier', False)
            or getattr(box, 'identificador', False)
            or box.display_name
            or ''
        )

    @api.onchange('ftth_service_id')
    def _onchange_ftth_service_id(self):
        if not self.ftth_service_id:
            return
        service = self.ftth_service_id
        if service.plan_id and not self.customer_plan_id:
            self.customer_plan_id = service.plan_id.id
        if service.onu_id and not self.onu_serial:
            self.onu_serial = service.onu_id.serial_number or ''
        if service.subinterface_id and not self.olt_interface:
            self.olt_interface = self._get_subinterface_code(service.subinterface_id)
        if service.box_id and not self.customer_box:
            self.customer_box = self._get_box_identifier(service.box_id)

    @api.onchange('incident_type_id')
    def _onchange_incident_type(self):
        """Sugerir prioridad, área y SLA (en horas exactas) según tipo de incidencia.
        
        SIEMPRE recalcula el SLA cuando cambia el síntoma, incluso si ya existe
        un SLA guardado. Esto es el comportamiento deseado:
          - Síntoma Crítico (6 h) → SLA = ahora + 6h
          - Síntoma Baja   (72 h) → SLA = ahora + 72h
        Las estrellas (priority) se actualizan automáticamente pero NO
        afectan el SLA por sí solas (solo el síntoma define el SLA).
        """
        if not self.incident_type_id:
            return
        inc = self.incident_type_id

        # ── 1. Actualizar estrellas (prioridad visual) según el síntoma ──────
        if inc.priority_suggestion:
            priority_map = {
                'Crítica': '3',
                'Muy Alta': '3',
                'Alta': '2',
                'Media': '1',
                'Baja': '0',
            }
            priority_name = inc.priority_suggestion.name
            self.priority = priority_map.get(priority_name, '1')
        
        # ── 2. Auto-asignar área desde el síntoma ────────────────────────────
        if inc.area_id:
            self.area_id = inc.area_id
        
        # ── 3. Recalcular SLA SIEMPRE que haya horas en el síntoma ──────────
        # Se recalcula incluso si ya hay un sla_deadline guardado, porque el
        # usuario cambió deliberadamente el síntoma y espera que el SLA se
        # ajuste al nuevo síntoma (Crítico=6h, Baja=72h, etc.).
        if inc.priority_suggestion and inc.priority_suggestion.hours_limit:
            hours = inc.priority_suggestion.hours_limit
            self.sla_mode = 'advanced'
            base = self.sla_start_datetime or fields.Datetime.now()
            if not self.sla_start_datetime:
                self.sla_start_datetime = base
            self.sla_end_datetime = base + timedelta(hours=hours)
            self.sla_deadline = self.sla_end_datetime

    @api.onchange('ticket_type_id')
    def _onchange_ticket_type_id(self):
        """Validar que el tipo de incidencia sea compatible con el tipo de ticket"""
        if not self.incident_type_id or not self.ticket_type_id:
            return
        # Verificar que el ticket_type_id del incident_type coincida con el seleccionado
        if self.incident_type_id.ticket_type_id != self.ticket_type_id:
            self.incident_type_id = False

    @api.onchange('area_id')
    def _onchange_area_id(self):
        if not self.area_id or not self.employee_id:
            return
        allowed_department_ids = self.env['hr.department'].search([
            ('id', 'child_of', self.area_id.id),
        ]).ids
        if self.employee_id.department_id.id not in allowed_department_ids:
            self.employee_id = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.user_id:
            self.user_id = self.employee_id.user_id
        if self.employee_id and self.employee_id.department_id and not self.area_id:
            self.area_id = self.employee_id.department_id

    @api.onchange('visit_diagnosis_id')
    def _onchange_visit_diagnosis_id(self):
        for ticket in self:
            if ticket.visit_diagnosis_id and not ticket.visit_diagnosis:
                ticket.visit_diagnosis = ticket.visit_diagnosis_id.name

    @api.onchange('visit_solution_id')
    def _onchange_visit_solution_id(self):
        for ticket in self:
            if ticket.visit_solution_id and not ticket.visit_solution:
                ticket.visit_solution = ticket.visit_solution_id.name

    @api.onchange('requires_visit')
    def _onchange_requires_visit(self):
        """Si desmarca "Requiere visita técnica", limpiar los campos de visita."""
        if not self.requires_visit:
            self.technician_id = False
            self.visit_date = False
            self.visit_result = 'pending'
        else:
            if not self.visit_date:
                self.visit_date = fields.Datetime.now()

    def _sync_visit_activity(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get_id('helpdesk.ticket')
        if not activity_type or not model_id:
            return

        for ticket in self:
            domain = [
                ('res_model_id', '=', model_id),
                ('res_id', '=', ticket.id),
                ('summary', '=', 'Visita tecnica programada'),
            ]
            activities = self.env['mail.activity'].search(domain)

            if not ticket.requires_visit or not ticket.technician_id:
                activities.unlink()
                continue
            
            visit_date_val = ticket.visit_date or fields.Datetime.now()

            note = (
                f"Ticket: {ticket.display_name}<br/>"
                f"Tecnico: {ticket.technician_id.name}<br/>"
                f"Fecha programada: {fields.Datetime.to_string(visit_date_val)}<br/>"
            )
            if ticket.visit_deadline:
                note += f"Fecha límite: {fields.Date.to_string(ticket.visit_deadline)}<br/>"
            if ticket.visit_notes:
                note += f"Notas: {ticket.visit_notes}<br/>"

            vals = {
                'activity_type_id': activity_type.id,
                'summary': 'Visita tecnica programada',
                'note': note,
                'user_id': ticket.technician_id.user_id.id if ticket.technician_id.user_id else self.env.uid,
                'date_deadline': ticket.visit_deadline if ticket.visit_deadline else fields.Date.to_date(visit_date_val),
                'res_id': ticket.id,
                'res_model_id': model_id,
            }

            if activities:
                activities.write(vals)
                if ticket.visit_ids and not ticket.visit_ids[0].activity_id:
                    ticket.visit_ids[0].activity_id = activities[0].id
            else:
                if vals.get('user_id') and ticket.visit_result in ('pending', 'in_progress', 'rescheduled'):
                    new_activity = self.env['mail.activity'].create(vals)
                    if ticket.visit_ids:
                        ticket.visit_ids[0].activity_id = new_activity.id

            if ticket.visit_result in ('done', 'cancelled'):
                self.env['mail.activity'].search(domain).action_feedback(
                    feedback='Visita tecnica cerrada en ticket.'
                )

            ticket.message_post(
                body=Markup(
                    '<b>Visita tecnica actualizada</b><br/>'
                    'Tecnico asignado: %s<br/>'
                    'Fecha programada: %s<br/>'
                    'Estado: %s'
                ) % (
                    ticket.technician_id.name,
                    fields.Datetime.to_string(ticket.visit_date),
                    dict(ticket._fields["visit_result"].selection).get(ticket.visit_result, "Pendiente"),
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def _prepare_postventa_activity_type_vals(self):
        vals = {
            'name': 'Postventa Helpdesk',
            'summary': 'Llamada de seguimiento postventa',
            'category': 'phonecall',
        }
        activity_type_model = self.env['mail.activity.type']
        if 'res_model' in activity_type_model._fields:
            vals['res_model'] = 'helpdesk.ticket'
        elif 'res_model_id' in activity_type_model._fields:
            vals['res_model_id'] = self.env['ir.model']._get_id('helpdesk.ticket')
        return vals

    def _get_postventa_activity_type(self):
        activity_type_model = self.env['mail.activity.type']
        domain = [('name', '=', 'Postventa Helpdesk')]
        if 'res_model' in activity_type_model._fields:
            domain.append(('res_model', '=', 'helpdesk.ticket'))
        elif 'res_model_id' in activity_type_model._fields:
            domain.append(('res_model_id.model', '=', 'helpdesk.ticket'))

        activity_type = activity_type_model.search(domain, limit=1)
        if activity_type:
            return activity_type
        return activity_type_model.create(self._prepare_postventa_activity_type_vals())

    def _sync_postventa_activity(self):
        model_id = self.env['ir.model']._get_id('helpdesk.ticket')
        if not model_id:
            return

        activity_type = self._get_postventa_activity_type()
        for ticket in self:
            domain = [
                ('res_model_id', '=', model_id),
                ('res_id', '=', ticket.id),
                ('activity_type_id', '=', activity_type.id),
                ('summary', '=', 'Llamada de seguimiento postventa'),
            ]
            activities = self.env['mail.activity'].search(domain, order='id desc')
            main_activity = activities[:1]

            if ticket.postventa_done:
                ticket.postventa_activity_id = False
                continue

            if not ticket.is_closed:
                activities.unlink()
                ticket.postventa_activity_id = False
                continue

            note = (
                f"Ticket: {ticket.display_name}<br/>"
                f"Cliente: {ticket.customer_name or '-'}<br/>"
                f"Codigo cliente: {ticket.customer_code or '-'}"
            )
            vals = {
                'activity_type_id': activity_type.id,
                'summary': 'Llamada de seguimiento postventa',
                'note': note,
                'user_id': ticket.user_id.id or self.env.user.id,
                'date_deadline': fields.Date.today(),
                'res_id': ticket.id,
                'res_model_id': model_id,
            }

            if main_activity:
                main_activity.write(vals)
                ticket.postventa_activity_id = main_activity.id
                (activities - main_activity).unlink()
            else:
                created = self.env['mail.activity'].create(vals)
                ticket.postventa_activity_id = created.id

    # =========================================================================
    # CRUD
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        cfg = self.env['helpdesk.sla.config'].get_config()
        
        priority_hours = {}
        for p in cfg.priority_sla_ids:
            if p.sequence == 50:
                priority_hours['3'] = p.hours_limit
            elif p.sequence == 20:
                priority_hours['2'] = p.hours_limit
            elif p.sequence == 30:
                priority_hours['1'] = p.hours_limit
            elif p.sequence == 40:
                priority_hours['0'] = p.hours_limit
        
        sla_by_priority = priority_hours
        critical_types = {'no_signal', 'fiber_cut', 'onu_offline'}
        
        # Establecer el ticket_type_id por defecto si no está especificado
        for vals in vals_list:
            if not vals.get('ticket_type_id'):
                # Buscar el tipo de ticket "incident" por défault
                default_type = self.env['helpdesk.ticket.type'].search(
                    [('code', '=', 'incident')], limit=1
                )
                if default_type:
                    vals['ticket_type_id'] = default_type.id
        
        for vals in vals_list:
            if vals.get('employee_id'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                if employee.department_id and not vals.get('area_id'):
                    vals['area_id'] = employee.department_id.id
                if employee.user_id and not vals.get('user_id'):
                    vals['user_id'] = employee.user_id.id
            if vals.get('ftth_service_id'):
                service = self.env['wigo.ftth.client.service'].browse(vals['ftth_service_id'])
                if service.plan_id and not vals.get('customer_plan_id'):
                    vals['customer_plan_id'] = service.plan_id.id
                if service.onu_id and not vals.get('onu_serial'):
                    vals['onu_serial'] = service.onu_id.serial_number or ''
                if service.subinterface_id and not vals.get('olt_interface'):
                    vals['olt_interface'] = self._get_subinterface_code(service.subinterface_id)
                if service.box_id and not vals.get('customer_box'):
                    vals['customer_box'] = self._get_box_identifier(service.box_id)
            now_dt = fields.Datetime.now()
            if not vals.get('name') or vals.get('name') in ('/', ''):
                vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or 'T-00001'
            vals.setdefault('date_open', now_dt)
            vals.setdefault('sla_start_datetime', vals.get('date_open') or now_dt)
            if not vals.get('stage_id'):
                first_stage = self.env['helpdesk.stage'].search([], order='sequence, id', limit=1)
                if first_stage:
                    vals['stage_id'] = first_stage.id
            # Auto-calcular SLA al crear si no fue especificado
            if not vals.get('sla_deadline'):
                base = vals.get('sla_start_datetime') or now_dt
                mode = vals.get('sla_mode') or 'advanced'

                if mode == 'advanced' and vals.get('sla_end_datetime'):
                    vals['sla_deadline'] = vals['sla_end_datetime']
                    continue

                quick_days = vals.get('sla_quick_days')
                if quick_days:
                    vals['sla_deadline'] = base + timedelta(days=int(quick_days))
                    vals.setdefault('sla_end_datetime', vals['sla_deadline'])
                    continue

                cat_id = vals.get('category_id')
                default_hours = sla_by_priority.get('1', 72.0)
                hours = default_hours
                if cat_id:
                    cat = self.env['helpdesk.category'].browse(cat_id)
                    if cat.sla_hours > 0:
                        hours = cat.sla_hours
                    else:
                        inc = vals.get('incident_type', '')
                        if inc in critical_types:
                            hours = sla_by_priority.get('3', 6.0)
                        else:
                            hours = sla_by_priority.get(vals.get('priority', '1'), default_hours)
                else:
                    inc_id = vals.get('incident_type_id')
                    inc_code = self.env['helpdesk.incident.type'].browse(inc_id).code if inc_id else ''
                    if inc_code in critical_types:
                        hours = sla_by_priority.get('3', 6.0)
                    else:
                        hours = sla_by_priority.get(vals.get('priority', '1'), default_hours)
                vals['sla_deadline'] = base + timedelta(hours=hours)

            if vals.get('sla_deadline') and not vals.get('sla_end_datetime'):
                vals['sla_end_datetime'] = vals['sla_deadline']
            if not vals.get('sla_start_datetime'):
                vals['sla_start_datetime'] = vals.get('create_date') or fields.Datetime.now()
        records = super().create(vals_list)
        for rec in records:
            if rec.create_date and rec.date_open != rec.create_date:
                rec.date_open = rec.create_date
            if rec.create_date and not rec.sla_start_datetime:
                rec.sla_start_datetime = rec.create_date
        records._sync_visit_activity()
        records._sync_postventa_activity()
        return records

    def write(self, vals):
        # NOTA: El campo priority (estrellas) es selección manual del usuario
        # y NO debe afectar el SLA. Solo el síntoma (incident_type_id) define el SLA.
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            if employee.department_id and not vals.get('area_id'):
                vals['area_id'] = employee.department_id.id
            if employee.user_id and not vals.get('user_id'):
                vals['user_id'] = employee.user_id.id
        if vals.get('ftth_service_id'):
            service = self.env['wigo.ftth.client.service'].browse(vals['ftth_service_id'])
            if service.plan_id and not vals.get('customer_plan_id'):
                vals['customer_plan_id'] = service.plan_id.id
            if service.onu_id and not vals.get('onu_serial'):
                vals['onu_serial'] = service.onu_id.serial_number or ''
            if service.subinterface_id and not vals.get('olt_interface'):
                vals['olt_interface'] = self._get_subinterface_code(service.subinterface_id)
            if service.box_id and not vals.get('customer_box'):
                vals['customer_box'] = self._get_box_identifier(service.box_id)

        if 'stage_id' in vals:
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            now = fields.Datetime.now()
            for ticket in self:
                if not ticket.date_open and not stage.is_close:
                    vals.setdefault('date_open', now)
            if stage.is_close:
                vals['date_closed'] = now
            else:
                vals['date_closed'] = False

        res = super().write(vals)

        if any(k in vals for k in ('requires_visit', 'visit_date', 'technician_id', 'visit_result', 'visit_ids')):
            self._sync_visit_activity()
        if any(k in vals for k in ('stage_id', 'postventa_done', 'postventa_date', 'postventa_user_id', 'satisfaction', 'postventa_notes', 'user_id')):
            self._sync_postventa_activity()
        return res

    # _recalculate_sla_on_priority_change fue eliminado intencionalmente.
    # Las estrellas (priority) son un campo visual/manual del usuario
    # y NO deben afectar el SLA. El SLA solo lo define el síntoma (incident_type_id).

    def _get_runtime_sla_status(self, now=None, cfg=None):
        """Calcula el estado SLA en tiempo real para un ticket."""
        self.ensure_one()
        now = now or fields.Datetime.now()
        cfg = cfg or self.env['helpdesk.sla.config'].get_config()

        if self.is_closed:
            return 'closed', 0.0
        if not self.sla_deadline:
            return 'ok', 0.0

        warn_pct = (cfg.warning_threshold_pct or 25.0) / 100.0
        warn_abs = cfg.warning_threshold_hours or 0.0

        start_dt = self.sla_start_datetime or self.date_open or self.create_date or now
        total_hours = (self.sla_deadline - start_dt).total_seconds() / 3600.0
        remaining = (self.sla_deadline - now).total_seconds() / 3600.0

        if remaining < 0:
            return 'danger', remaining

        in_warning_pct = total_hours > 0 and (remaining / total_hours) < warn_pct
        in_warning_abs = warn_abs > 0 and remaining < warn_abs
        return ('warning' if (in_warning_pct or in_warning_abs) else 'ok'), remaining

    def _build_sla_transition_message(self, status, remaining_hours, cfg):
        """Arma el mensaje chatter cuando el semáforo SLA cambia de estado."""
        self.ensure_one()
        labels = {
            'ok': cfg.ok_label or 'En tiempo',
            'warning': cfg.warning_label or 'Próximo a vencer',
            'danger': cfg.danger_label or 'SLA Vencido',
            'closed': cfg.closed_label or 'Cerrado',
        }
        icons = {
            'ok': '🟢',
            'warning': '🟡',
            'danger': '🔴',
            'closed': '⚪',
        }

        if status == 'closed':
            return _('%(icon)s <strong>SLA %(label)s.</strong> El ticket fue cerrado.') % {
                'icon': icons[status],
                'label': labels[status],
            }

        total_minutes = int(round(abs(remaining_hours or 0.0) * 60))
        hours, minutes = divmod(total_minutes, 60)
        if (remaining_hours or 0.0) < 0:
            remaining_text = _('Vencido por %(h)s h %(m)02d min') % {'h': hours, 'm': minutes}
        else:
            remaining_text = _('Restan %(h)s h %(m)02d min') % {'h': hours, 'm': minutes}

        return _('%(icon)s <strong>SLA %(label)s.</strong> %(remaining)s.') % {
            'icon': icons.get(status, 'ℹ️'),
            'label': labels.get(status, 'actualizado'),
            'remaining': remaining_text,
        }

    # =========================================================================
    # CRON — Cambio automático de etapa al vencer SLA
    # =========================================================================
    @api.model
    def _cron_check_sla_deadline(self):
        """Notifica transiciones del semáforo SLA y escala tickets vencidos sin repetir avisos.
        También recalcula sla_progress_pct y sla_status para todos los tickets abiertos
        con deadline, ya que el tiempo pasa pero los campos depend de fechas estáticas.
        """
        now = fields.Datetime.now()
        cfg = self.env['helpdesk.sla.config'].get_config()
        tickets = self.search([
            '|',
            ('sla_deadline', '!=', False),
            ('sla_last_notified_status', '!=', False),
        ])
        if not tickets:
            return

        # ── Forzar recomputación de sla_progress_pct y sla_status ──────────────
        # Estos campos son store=True con depends en campos de fecha estáticos.
        # Odoo no los recalcula automáticamente cuando pasa el tiempo, por eso
        # el cron los invalida explicitamente para forzar el recompute.
        tickets.invalidate_recordset(['sla_progress_pct', 'sla_status',
                                      'sla_exceeded', 'sla_hours_remaining'])
        tickets._compute_sla_progress_pct()
        tickets._compute_sla_status()
        tickets._compute_sla_exceeded()

        waiting_stage = self.env['helpdesk.stage'].search([('name', '=', 'En Espera')], limit=1)

        for ticket in tickets:
            runtime_status, remaining = ticket._get_runtime_sla_status(now=now, cfg=cfg)
            previous_status = ticket.sla_last_notified_status

            # Primera vez: inicializa estado base sin generar spam histórico.
            if not previous_status:
                ticket.with_context(tracking_disable=True).write({
                    'sla_last_notified_status': runtime_status,
                    'sla_last_notified_at': now,
                })
            elif previous_status != runtime_status:
                should_notify = (runtime_status != 'warning') or bool(cfg.notify_on_warning)
                if should_notify:
                    ticket.message_post(
                        body=ticket._build_sla_transition_message(runtime_status, remaining, cfg),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )

                ticket.with_context(tracking_disable=True).write({
                    'sla_last_notified_status': runtime_status,
                    'sla_last_notified_at': now,
                })

            if (
                runtime_status == 'danger'
                and cfg.escalate_on_expire
                and waiting_stage
                and not ticket.is_closed
                and ticket.stage_id.id != waiting_stage.id
            ):
                ticket.write({'stage_id': waiting_stage.id})

    # =========================================================================
    # ACCIONES DE BOTONES
    # =========================================================================
    def action_open(self):
        stage = self.env['helpdesk.stage'].search([('is_close', '=', False)], order='sequence, id', limit=1)
        if not stage:
            raise UserError(_('No hay etapas abiertas configuradas.'))
        self.write({'stage_id': stage.id})

    def action_resolve(self):
        stage = self.env['helpdesk.stage'].search(
            [('is_close', '=', False), ('sequence', '>=', 20)], order='sequence, id', limit=1,
        )
        if not stage:
            stage = self.env['helpdesk.stage'].search(
                [('is_close', '=', False)], order='sequence desc, id desc', limit=1
            )
        if not stage:
            raise UserError(_('No hay etapas disponibles.'))
        self.write({'stage_id': stage.id})

    def action_close(self):
        stage = self.env['helpdesk.stage'].search([('is_close', '=', True)], order='sequence, id', limit=1)
        if not stage:
            raise UserError(_('No hay etapas de cierre configuradas.'))
        self.write({'stage_id': stage.id})

    def action_assign_to_me(self):
        employee = self.env.user.employee_id
        if not employee:
            raise UserError(_('Tu usuario no tiene un empleado vinculado en Recursos Humanos.'))
        vals = {'user_id': self.env.uid, 'employee_id': employee.id}
        if employee.department_id:
            vals['area_id'] = employee.department_id.id
        self.write(vals)

    def action_escalate(self):
        return {
            'name': _('Escalar Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ticket_id': self.id, 'escalate_mode': True},
        }

    def action_mark_postventa(self):
        self.ensure_one()
        model_id = self.env['ir.model']._get_id('helpdesk.ticket')
        activity_type = self._get_postventa_activity_type()
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', model_id),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
            ('summary', '=', 'Llamada de seguimiento postventa'),
        ], limit=1)

        if not activity:
            activity = self.env['mail.activity'].create({
                'res_model_id': model_id,
                'res_id': self.id,
                'activity_type_id': activity_type.id,
                'summary': 'Llamada de seguimiento postventa',
                'date_deadline': fields.Date.today(),
                'user_id': self.user_id.id or self.env.user.id,
                'note': (
                    f"Ticket: {self.display_name}<br/>"
                    f"Cliente: {self.customer_name or '-'}<br/>"
                    f"Codigo cliente: {self.customer_code or '-'}"
                ),
            })
        self.postventa_activity_id = activity.id

        return {
            'name': _('Actividad de Postventa'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'res_id': activity.id,
            'target': 'new',
            'context': {'default_res_model_id': model_id, 'default_res_id': self.id},
        }

    def action_open_sla_advanced_wizard(self):
        self.ensure_one()
        return {
            'name': _('Configurar SLA del Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.sla.advanced.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            },
        }

    # =========================================================================
    # KANBAN GROUP EXPAND
    # =========================================================================
    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Muestra todas las etapas en Kanban aunque estén vacías. Odoo 17+/19."""
        return self.env['helpdesk.stage'].search([], order='sequence, id')
