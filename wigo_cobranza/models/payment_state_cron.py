from datetime import date, timedelta
from calendar import monthrange
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class WigoPagoEstadoCron(models.Model):
    _inherit = 'wigo.pago.estado'

    # ═══════════════════════════════════════════════════════════
    # Period Suggestion
    # ═══════════════════════════════════════════════════════════

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
            mes_sugerido, anio_sugerido = self._suggest_next_period_values(
                contract=rec.contract_id,
                client_service=rec.client_service_id,
                partner=rec.partner_id,
            )
            rec.mes = mes_sugerido
            rec.anio = anio_sugerido

    # ═══════════════════════════════════════════════════════════
    # Due Date Calculation
    # ═══════════════════════════════════════════════════════════

    def _add_months_to_date(self, base_date, months_to_add):
        month = base_date.month + months_to_add
        year = base_date.year

        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1

        _, max_day = monthrange(year, month)
        day = min(base_date.day, max_day)

        return date(year, month, day)

    def _get_period_start_date(self, mes_facturado, anio_facturado):
        try:
            mes_int = int(mes_facturado)
            anio_int = int(anio_facturado)
            fecha_inicio = date(anio_int, mes_int, 1)
            _logger.info(
                f"Period start date: {fecha_inicio} for month {mes_int} year {anio_int}"
            )
            return fecha_inicio
        except Exception as e:
            _logger.error(f"Error getting period start date: {e}")
            return False

    def _calculate_due_date(self, mes_facturado, anio_facturado, rule):
        try:
            fecha_inicio_periodo = self._get_period_start_date(
                mes_facturado, anio_facturado
            )
            if not fecha_inicio_periodo:
                return False

            if rule.mora_criterio == 'meses':
                meses_a_agregar = int(rule.meses_mora or 0)
                fecha_vencimiento = self._add_months_to_date(
                    fecha_inicio_periodo, meses_a_agregar
                )
            else:
                dias_a_agregar = int(rule.dias_mora or 0)
                fecha_vencimiento = fecha_inicio_periodo + timedelta(days=dias_a_agregar)

            _logger.info(f"Due date: {fecha_vencimiento}")
            return fecha_vencimiento

        except Exception as e:
            _logger.error(f"Error calculating due date: {e}")
            return False

    def _calculate_billed_period_from_trigger_day(self, rule, today=None):
        today = today or date.today()
        trigger_day = int(rule.dia_generacion)
        current_day = today.day
        current_month = today.month
        current_year = today.year

        if current_day >= trigger_day:
            return current_month, current_year

        if current_month == 1:
            return 12, current_year - 1
        return current_month - 1, current_year

    # ═══════════════════════════════════════════════════════════
    # Overdue / Mora Helpers
    # ═══════════════════════════════════════════════════════════

    def _months_overdue(self, rec, today=None):
        today = today or date.today()
        if not rec or not rec.fecha_vencimiento:
            return 0
        due = rec.fecha_vencimiento
        months = (today.year - due.year) * 12 + (today.month - due.month)
        if today.day < due.day:
            months -= 1
        return max(months, 0)

    def _months_between_dates(self, start_date, end_date=None):
        end_date = end_date or date.today()
        if not start_date:
            return 0
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if end_date.day < start_date.day:
            months -= 1
        return max(months, 0)

    def _get_active_contracts_for_rule(self, rule):
        Contract = self.env['customer.contract']
        domain = [('state', '=', 'active')]
        if rule.payment_mode and rule.payment_mode != 'all':
            domain.append(('payment_mode', '=', rule.payment_mode))
        return Contract.search(domain, order='partner_id, id')

    def _get_existing_payment_for_period(
        self, contract=None, client_service=None,
        partner=None, mes=None, anio=None,
    ):
        domain = []
        if mes is not None:
            domain.append(('mes', '=', str(mes)))
        if anio is not None:
            domain.append(('anio', '=', int(anio)))

        if contract:
            domain.append(('contract_id', '=', contract.id))
        elif client_service:
            domain.append(('client_service_id', '=', client_service.id))
        elif partner:
            domain.append(('partner_id', '=', partner.id))
        else:
            return self.browse()

        return self.search(domain, limit=1, order='id desc')

    # ═══════════════════════════════════════════════════════════
    # Generation
    # ═══════════════════════════════════════════════════════════

    def _build_generation_vals(self, contract, rule, today):
        service = self._find_client_service_for_contract(contract)
        mes_facturado, anio_facturado = self._calculate_billed_period_from_trigger_day(rule, today)
        fecha_vencimiento = self._calculate_due_date(mes_facturado, anio_facturado, rule)

        vals = {
            'partner_id': contract.partner_id.id,
            'contract_id': contract.id,
            'mes': str(mes_facturado),
            'anio': anio_facturado,
            'estado_pago': rule.estado_inicial,
            'fecha_pago': fields.Date.context_today(self),
            'generado_automaticamente': True,
        }

        if fecha_vencimiento:
            _logger.info(
                f"Period: {mes_facturado}/{anio_facturado}, "
                f"due date calculated: {fecha_vencimiento}"
            )

        if service:
            vals['client_service_id'] = service.id
        return vals

    def _cron_generar_deudas_diarias(self, today=None):
        if today is None:
            today_dt = fields.Datetime.context_timestamp(
                self.with_context(tz='America/La_Paz'),
                fields.Datetime.now()
            )
            today = today_dt.date()
        rules = self.env['wigo.cobranza.regla']._get_generation_rules_for_day(today.day)
        if not rules:
            return 0

        created = 0
        seen_contracts = set()
        for rule in rules:
            contracts = self._get_active_contracts_for_rule(rule)
            mes_facturado, anio_facturado = self._calculate_billed_period_from_trigger_day(rule, today)

            for contract in contracts:
                if contract.id in seen_contracts:
                    continue
                seen_contracts.add(contract.id)

                existing = self._get_existing_payment_for_period(
                    contract=contract,
                    mes=str(mes_facturado),
                    anio=anio_facturado,
                )
                if existing:
                    continue

                vals = self._build_generation_vals(contract, rule, today)
                self.create(vals)
                created += 1

        if created:
            self._notify_cobranza_group(
                f"Se generaron {created} registros de cobro pendientes "
                f"para el período {today.strftime('%B %Y')}. "
                f"Por favor inicie la gestión de cobro."
            )
        return created

    # ═══════════════════════════════════════════════════════════
    # Mora Evaluation
    # ═══════════════════════════════════════════════════════════

    def _get_open_payments_for_rules_mora(self, today=None):
        return self.search([
            ('estado_pago', 'in', ['pendiente', 'mora']),
            ('contract_id', '!=', False),
        ], order='fecha_vencimiento asc, id asc')

    def _get_open_payments_for_rules_incobrables(self, today=None):
        return self.search([
            ('estado_pago', 'in', ['mora']),
            ('contract_id', '!=', False),
        ], order='fecha_vencimiento asc, id asc')

    def _cron_evaluar_mora_diaria(self, today=None):
        if today is None:
            today_dt = fields.Datetime.context_timestamp(
                self.with_context(tz='America/La_Paz'),
                fields.Datetime.now()
            )
            today = today_dt.date()
        pagos = self._get_open_payments_for_rules_mora(today)
        mora_count = 0
        for rec in pagos:
            regla = self._get_regla_for_contract(rec.contract_id)
            if not regla:
                continue

            overdue_date = self._calculate_due_date(rec.mes, rec.anio, regla)
            if not overdue_date:
                continue

            if today >= overdue_date and rec.estado_pago != 'mora':
                rec.write({'estado_pago': 'mora'})
                mora_count += 1
                self._notify_mora(rec, regla)

        return mora_count

    # ═══════════════════════════════════════════════════════════
    # Uncollectible Evaluation
    # ═══════════════════════════════════════════════════════════

    def _cron_evaluar_incobrables_diario(self, today=None):
        if today is None:
            today_dt = fields.Datetime.context_timestamp(
                self.with_context(tz='America/La_Paz'),
                fields.Datetime.now()
            )
            today = today_dt.date()
        _logger.info(f"Evaluating uncollectibles for open payments as of {today}")

        pagos = self._get_open_payments_for_rules_incobrables(today)
        contracts = pagos.mapped('contract_id')
        contracts_to_check = set()

        for contract in contracts:
            regla = self._get_regla_for_contract(contract)
            if not regla:
                continue

            if regla.incobrable_criterio == 'meses':
                cantidad_mora = self.search_count([
                    ('contract_id', '=', contract.id),
                    ('estado_pago', '=', 'mora'),
                ])
                _logger.info(
                    "Contract %s has %s overdue payments",
                    contract.name, cantidad_mora,
                )
                supera_incobrable = cantidad_mora >= (regla.meses_incobrable or 0)
                _logger.info(f"Exceeds uncollectible: {supera_incobrable}, threshold: {regla.meses_incobrable}")
            else:
                pagos_mora = self.search([
                    ('contract_id', '=', contract.id),
                    ('estado_pago', '=', 'mora'),
                ], order='fecha_vencimiento asc', limit=1)

                if not pagos_mora:
                    continue

                pago_mas_antiguo = pagos_mora[0]
                overdue_date = self._calculate_due_date(
                    pago_mas_antiguo.mes, pago_mas_antiguo.anio, regla,
                )
                if not overdue_date:
                    continue

                dias_atraso = max((today - overdue_date).days, 0)
                _logger.info(
                    "Contract %s has %s days overdue", contract.name, dias_atraso,
                )
                supera_incobrable = dias_atraso >= (regla.dias_incobrable or 0)

            if supera_incobrable:
                contracts_to_check.add(contract.id)

        for contract_id in contracts_to_check:
            contract = self.env['customer.contract'].browse(contract_id)
            self._check_create_incobrable_from_contract(contract)

        _logger.info(
            "Total contracts sent to uncollectibles: %s", len(contracts_to_check),
        )
        return len(contracts_to_check)

    # ═══════════════════════════════════════════════════════════
    # Master Cron
    # ═══════════════════════════════════════════════════════════

    @api.model
    def cron_procesar_cobranza(self):
        _logger.warning("=== COLLECTION CRON EXECUTED ===")
        today_dt = fields.Datetime.context_timestamp(
            self.with_context(tz='America/La_Paz'),
            fields.Datetime.now()
        )
        today = today_dt.date()
        self._deactivate_legacy_crons()
        generados = self._cron_generar_deudas_diarias(today=today)
        moras = self._cron_evaluar_mora_diaria(today=today)
        incobrables = self._cron_evaluar_incobrables_diario(today=today)
        return {
            'date': today.isoformat(),
            'generated': generados,
            'mora_updated': moras,
            'incobrables_checked': incobrables,
        }

    # ═══════════════════════════════════════════════════════════
    # Notifications
    # ═══════════════════════════════════════════════════════════

    def _notify_cobranza_group(self, body, model='wigo.pago.estado', res_id=False):
        group = self.env.ref('wigo_cobranza.group_cobranza', raise_if_not_found=False)
        if not group:
            return
        partners = group.user_ids.mapped('partner_id')
        if not partners:
            return
        self.env['mail.message'].create({
            'message_type': 'notification',
            'body': body,
            'partner_ids': partners.ids,
            'model': model,
            'res_id': res_id,
        })

    def _notify_mora(self, rec, regla):
        cobranza_group = self.env.ref(
            'wigo_cobranza.group_cobranza', raise_if_not_found=False
        )
        if cobranza_group:
            partners = cobranza_group.user_ids.mapped('partner_id')
            if partners:
                self.env['mail.message'].create({
                    'message_type': 'notification',
                    'body': (
                        f"Cliente {rec.partner_id.name} en mora. "
                        f"Días de atraso: {rec.dias_atraso}. "
                        f"Regla: {regla.name}."
                    ),
                    'partner_ids': partners.ids,
                    'model': 'wigo.pago.estado',
                    'res_id': rec.id,
                })

    def _deactivate_legacy_crons(self):
        cron_xmlids = [
            'wigo_cobranza.cron_alertar_mora_dia1',
            'wigo_cobranza.cron_evaluar_cobranza',
            'wigo_cobranza.cron_detectar_incobrables',
            'wigo_cobranza.cron_alertar_suspension',
        ]
        for xmlid in cron_xmlids:
            cron = self.env.ref(xmlid, raise_if_not_found=False)
            if cron and cron.active:
                cron.sudo().write({'active': False})

    # ═══════════════════════════════════════════════════════════
    # Contract Mora Recomputation
    # ═══════════════════════════════════════════════════════════

    def _recompute_contract_mora(self):
        contracts = self.mapped('contract_id').filtered(lambda c: c)
        if not contracts:
            return
        from datetime import date as _date

        for contract in contracts:
            pagos = self.search([('contract_id', '=', contract.id)])
            today = _date.today()
            regla_contrato = self._get_regla_for_contract(contract)

            for rec in pagos:
                try:
                    if rec.estado_pago == 'pagado':
                        continue

                    fecha_venc = False
                    if regla_contrato:
                        fecha_venc = self._calculate_due_date(
                            rec.mes, rec.anio, regla_contrato
                        )
                    else:
                        fecha_venc = rec.fecha_vencimiento

                    if not fecha_venc:
                        continue

                    if today < fecha_venc:
                        continue
                except Exception:
                    continue

            unpaid = pagos.filtered(
                lambda p: p.estado_pago in ('pendiente', 'mora')
            )
            if len(unpaid) >= 3:
                latest = unpaid.sorted(
                    key=lambda r: (r.anio or 0, int(r.mes or 0), r.id),
                    reverse=True,
                )[:1]
                latest_rec = latest and latest[0] or False
                service = (
                    latest_rec.client_service_id
                    if latest_rec
                    else self._find_client_service_for_contract(contract)
                )
                if service:
                    vals = {}
                    if (
                        'estado_servicio' in service._fields
                        and service.estado_servicio != 'baja'
                    ):
                        vals['estado_servicio'] = 'suspended'
                    if vals:
                        service.write(vals)

                regla = self._get_regla_for_contract(contract)
                if regla:
                    self._check_create_incobrable_from_contract(contract)

    def _check_create_incobrable_from_contract(self, contract):
        if not contract:
            return

        regla = self._get_regla_for_contract(contract)
        if not regla:
            return

        Incobrable = self.env['wigo.incobrable'].sudo()

        pagos_mora = self.search([
            ('contract_id', '=', contract.id),
            ('estado_pago', '=', 'mora'),
        ], order='anio asc, mes asc')

        if not pagos_mora:
            return

        cantidad_periodos = len(pagos_mora)
        monto_total = sum(pagos_mora.mapped('monto_a_cobrar'))
        periodos = ', '.join(pagos_mora.mapped('periodo'))
        svc = self._find_client_service_for_contract(contract)

        ya_existe = Incobrable.search([
            ('partner_id', '=', contract.partner_id.id),
            ('contract_id', '=', contract.id),
            ('state', 'not in', ['recuperado']),
        ], limit=1)

        if ya_existe:
            ya_existe.write({
                'meses_adeudados': periodos,
                'monto_total_adeudado': monto_total,
                'observaciones': (
                    f'Actualizado automáticamente: '
                    f'{cantidad_periodos} períodos en mora. '
                    f'Modalidad: {regla.name}.'
                ),
            })
            _logger.info("Uncollectible updated for contract %s", contract.name)
            return ya_existe

        incobrable = Incobrable.create({
            'partner_id': contract.partner_id.id,
            'contract_id': contract.id,
            'client_service_id': svc.id if svc else False,
            'meses_adeudados': periodos,
            'monto_total_adeudado': monto_total,
            'state': 'activo',
            'observaciones': (
                f'Generado automáticamente: '
                f'{cantidad_periodos} períodos en mora. '
                f'Modalidad: {regla.name}.'
            ),
        })

        _logger.info("Uncollectible created for contract %s", contract.name)

        if svc:
            svc.message_post(
                body=(
                    f"Cliente trasladado a incobrables automáticamente. "
                    f"Código: {svc.codigo_cliente} -- "
                    f"{svc.partner_id.name}. "
                    f"Períodos en mora: {periodos}."
                ),
                subtype_xmlid='mail.mt_comment',
                partner_ids=self._get_tech_partner_ids(),
            )

        cobranza_group = self.env.ref(
            'wigo_cobranza.group_cobranza', raise_if_not_found=False
        )
        if cobranza_group:
            partners = cobranza_group.user_ids.mapped('partner_id')
            if partners:
                self.env['mail.message'].sudo().create({
                    'message_type': 'notification',
                    'body': (
                        f"{contract.partner_id.name} "
                        f"trasladado a incobrables "
                        f"por {cantidad_periodos} períodos en mora."
                    ),
                    'partner_ids': partners.ids,
                    'model': 'wigo.incobrable',
                    'res_id': incobrable.id,
                })

        return incobrable
