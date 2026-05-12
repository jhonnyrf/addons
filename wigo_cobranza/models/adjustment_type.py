from odoo import api, fields, models


class WigoCobranzaTipoAjuste(models.Model):
    _name = 'wigo.cobranza.tipo_ajuste'
    _description = 'Adjustment Type'
    _order = 'is_default desc, name asc, id asc'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    is_default = fields.Boolean(string='Por defecto', default=False, tracking=True)
    color = fields.Integer(string='Color', default=1)
    requires_reason = fields.Boolean(string='Requiere motivo', default=False, tracking=True)
    enable_proration = fields.Boolean(string='Habilita prorrateo', default=False, tracking=True)

    def _normalize_legacy_color_values(self):
        self.env.cr.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'wigo_cobranza_tipo_ajuste'
              AND column_name = 'color'
        """)
        col = self.env.cr.fetchone()
        if col and col[0] in ('character varying', 'text', 'character'):
            self.env.cr.execute("""
                UPDATE wigo_cobranza_tipo_ajuste
                SET color = '0'
                WHERE color IS NULL
                   OR btrim(color) = ''
                   OR color !~ '^[0-9]+$'
            """)

    def _auto_init(self):
        self._normalize_legacy_color_values()
        return super()._auto_init()

    def init(self):
        self._normalize_legacy_color_values()
        self.env.cr.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'wigo_cobranza_tipo_ajuste'
              AND column_name = 'color'
        """)
        col = self.env.cr.fetchone()
        if col and col[0] not in ('integer', 'smallint', 'bigint'):
            self.env.cr.execute("""
                ALTER TABLE wigo_cobranza_tipo_ajuste
                ALTER COLUMN color TYPE integer
                USING CASE
                    WHEN color ~ '^[0-9]+$' THEN color::integer
                    ELSE 0
                END
            """)

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('is_default') for vals in vals_list):
            others = self.search([('is_default', '=', True)])
            if others:
                others.write({'is_default': False})
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('is_default'):
            others = self.search([
                ('id', 'not in', self.ids),
                ('is_default', '=', True),
            ])
            if others:
                others.write({'is_default': False})
        return super().write(vals)
