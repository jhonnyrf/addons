# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InternetPlan(models.Model):
    _name = 'internet.plan'
    _description = 'Plan de Internet'
    _order = 'plan_type, download_speed desc'

    name = fields.Char(string="Nombre del plan", required=True)
    plan_identifier = fields.Char(string="Identificador", copy=False)
    download_speed = fields.Integer(string="Velocidad DOWN (Mbps)")
    upload_speed = fields.Float(string="Velocidad UP (Mbps)")
    speed = fields.Integer(string="Velocidad (Mbps)", required=True)
    price = fields.Float(string="Tarifa mensual (Bs)", required=True)
    plan_type = fields.Selection([
        ('fiber', 'Fibra óptica'),
    ], string="Tipo", required=True, default='fiber')
    active = fields.Boolean(string="Activo", default=True, required=True)
    description = fields.Text(string="Descripción")

    _sql_constraints = [
        ('internet_plan_identifier_uniq', 'unique(plan_identifier)', 'El identificador del plan ya existe.'),
    ]

    @api.onchange('download_speed')
    def _onchange_download_speed(self):
        for rec in self:
            if rec.download_speed and not rec.speed:
                rec.speed = rec.download_speed

    @api.onchange('speed')
    def _onchange_speed(self):
        for rec in self:
            if rec.speed and not rec.download_speed:
                rec.download_speed = rec.speed

    @api.constrains('speed')
    def _check_speed(self):
        for record in self:
            if record.speed <= 0:
                raise ValidationError("La velocidad debe ser mayor que 0.")

    @api.constrains('download_speed')
    def _check_download_speed(self):
        for record in self:
            if record.download_speed <= 0:
                raise ValidationError("La velocidad DOWN debe ser mayor que 0.")

    @api.constrains('upload_speed')
    def _check_upload_speed(self):
        for record in self:
            if record.upload_speed <= 0:
                raise ValidationError("La velocidad UP debe ser mayor que 0.")

    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError("El precio debe ser mayor que 0 Bs.")
            if record.price > 10000:
                raise ValidationError("El precio no puede ser mayor a 10 000 Bs.")

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name and len(record.name.strip()) < 3:
                raise ValidationError("El nombre del plan debe tener al menos 3 caracteres.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'active' not in vals:
                vals['active'] = True
            if vals.get('download_speed') and not vals.get('speed'):
                vals['speed'] = vals['download_speed']
            if vals.get('speed') and not vals.get('download_speed'):
                vals['download_speed'] = vals['speed']
            if not vals.get('plan_identifier') and vals.get('name'):
                vals['plan_identifier'] = vals['name'].strip()
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if vals.get('download_speed') and 'speed' not in vals:
            vals['speed'] = vals['download_speed']
        if vals.get('speed') and 'download_speed' not in vals:
            vals['download_speed'] = vals['speed']
        return super().write(vals)

    def action_save_plan(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'Plan guardado correctamente.',
                'type': 'success',
                'sticky': False,
            },
        }
