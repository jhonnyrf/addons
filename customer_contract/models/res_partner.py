from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # =========================================================
    # RELACIÓN CON CONTRATOS
    # =========================================================
    contract_ids = fields.One2many(
        'customer.contract',
        'partner_id',
        string='Contratos',
    )
    contract_count = fields.Integer(
        string='Cantidad de Contratos',
        compute='_compute_contract_count',
        store=False,
    )

    # =========================================================
    # COMPUTED
    # =========================================================
    @api.depends('contract_ids')
    def _compute_contract_count(self):
        # read_group para eficiencia cuando hay muchos registros en lista
        domain = [('partner_id', 'in', self.ids)]
        groups = self.env['customer.contract'].read_group(
            domain, ['partner_id'], ['partner_id']
        )
        count_map = {g['partner_id'][0]: g['partner_id_count'] for g in groups}
        for partner in self:
            partner.contract_count = count_map.get(partner.id, 0)

    # =========================================================
    # ACCIÓN — abrir contratos del contacto
    # =========================================================
    def action_view_contracts(self):
        self.ensure_one()
        action = {
            'type':      'ir.actions.act_window',
            'name':      f'Contratos de {self.name}',
            'res_model': 'customer.contract',
            'view_mode': 'tree,form,kanban',
            'domain':    [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id':        self.id,
                'search_default_partner_id': self.id,
            },
        }
        # Si tiene exactamente uno, abre directo el formulario
        if self.contract_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.contract_ids[0].id
        return action