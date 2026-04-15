# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    is_post_sale = fields.Boolean(
        string='Posventa CRM',
        compute='_compute_is_post_sale',
        inverse='_inverse_is_post_sale',
        search='_search_is_post_sale',
        store=False,
        help='Marca el tipo de actividad para llamadas de seguimiento posventa.',
    )

    def _compute_is_post_sale(self):
        if not self._has_post_sale_rel_table():
            for record in self:
                record.is_post_sale = False
            return
        rel_model = self.env['crm.post.sale.activity.type']
        rels = rel_model.search([('activity_type_id', 'in', self.ids)])
        post_sale_ids = set(rels.mapped('activity_type_id').ids)
        for record in self:
            record.is_post_sale = record.id in post_sale_ids

    def _inverse_is_post_sale(self):
        if not self._has_post_sale_rel_table():
            return
        rel_model = self.env['crm.post.sale.activity.type']
        for record in self:
            rel = rel_model.search([('activity_type_id', '=', record.id)], limit=1)
            if record.is_post_sale and not rel:
                rel_model.create({'activity_type_id': record.id})
            elif not record.is_post_sale and rel:
                rel.unlink()

    def _search_is_post_sale(self, operator, value):
        if not self._has_post_sale_rel_table():
            if (operator in ('=', '==') and value) or (operator in ('!=', '<>') and not value):
                return [('id', '=', 0)]
            return []
        rel_model = self.env['crm.post.sale.activity.type']
        post_sale_ids = rel_model.search([]).mapped('activity_type_id').ids
        if operator in ('=', '=='):
            return [('id', 'in' if value else 'not in', post_sale_ids)]
        if operator in ('!=', '<>'):
            return [('id', 'not in' if value else 'in', post_sale_ids)]
        return [('id', '=', 0)]

    def _has_post_sale_rel_table(self):
        self.env.cr.execute("SELECT to_regclass('crm_post_sale_activity_type')")
        return bool(self.env.cr.fetchone()[0])

    def _get_target_model_name(self):
        self.ensure_one()
        if 'res_model' in self._fields:
            return self.res_model
        if 'res_model_id' in self._fields and self.res_model_id:
            return self.res_model_id.model
        return False

    def _set_target_model_in_vals(self, vals, model_name):
        if 'res_model' in self._fields:
            vals['res_model'] = model_name
        elif 'res_model_id' in self._fields:
            vals['res_model_id'] = self.env['ir.model']._get(model_name).id
        return vals

    def _get_crm_domain(self):
        if 'res_model' in self._fields:
            return [('res_model', '=', 'crm.lead')]
        if 'res_model_id' in self._fields:
            return [('res_model_id.model', '=', 'crm.lead')]
        return [('id', '=', 0)]

    def _get_cancellation_domain_by_name(self, name):
        domain = [('name', '=', name)]
        if 'res_model' in self._fields:
            domain.append(('res_model', '=', 'service.cancellation'))
        elif 'res_model_id' in self._fields:
            domain.append(('res_model_id.model', '=', 'service.cancellation'))
        return domain

    def _prepare_cancellation_vals(self):
        self.ensure_one()
        field_names = [
            'name',
            'summary',
            'icon',
            'decoration_type',
            'delay_count',
            'delay_unit',
            'delay_from',
            'default_user_id',
            'category',
            'chaining_type',
            'active',
        ]
        vals = {}
        for field_name in field_names:
            if field_name in self._fields:
                if self._fields[field_name].type == 'many2one':
                    vals[field_name] = self[field_name].id
                else:
                    vals[field_name] = self[field_name]
        self._set_target_model_in_vals(vals, 'service.cancellation')
        return vals

    def _ensure_cancellation_type(self):
        for record in self:
            if record._get_target_model_name() != 'crm.lead':
                continue

            vals = record._prepare_cancellation_vals()
            mirror = record.search(record._get_cancellation_domain_by_name(record.name), limit=1)
            if mirror:
                mirror.with_context(skip_cancellation_activity_type_sync=True).write(vals)
            else:
                record.with_context(skip_cancellation_activity_type_sync=True).create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.env.context.get('skip_cancellation_activity_type_sync'):
            return records
        for record in records:
            if any('is_post_sale' in vals for vals in vals_list):
                record._inverse_is_post_sale()
            record._ensure_cancellation_type()
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_cancellation_activity_type_sync'):
            return res
        for record in self:
            if 'is_post_sale' in vals:
                record._inverse_is_post_sale()
            record._ensure_cancellation_type()
        return res

    def _register_hook(self):
        res = super()._register_hook()
        if self._has_post_sale_rel_table():
            self._ensure_default_post_sale_type()
        for activity_type in self.search(self._get_crm_domain()):
            activity_type._ensure_cancellation_type()
        return res

    def _ensure_default_post_sale_type(self):
        domain = [('name', '=', 'Posventa CRM')]
        if 'res_model' in self._fields:
            domain.append(('res_model', '=', 'crm.lead'))
        elif 'res_model_id' in self._fields:
            domain.append(('res_model_id.model', '=', 'crm.lead'))

        activity_type = self.search(domain, limit=1)
        vals = {
            'name': 'Posventa CRM',
            'summary': 'Llamada de seguimiento postventa',
            'category': 'phonecall',
        }
        self._set_target_model_in_vals(vals, 'crm.lead')

        if activity_type:
            activity_type.write(vals)
            activity_type.write({'is_post_sale': True})
        else:
            created = self.create(vals)
            created.write({'is_post_sale': True})