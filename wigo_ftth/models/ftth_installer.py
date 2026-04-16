from odoo import models, fields, api


class FtthInstaller(models.Model):
    """Technician or external installation company."""
    
    _name = 'wigo.ftth.installer'
    _description = 'Técnico / Empresa Instaladora'
    _order = 'name'

    # ═════════════════════════════════════════════════════════════════════════════
    # Core Fields
    # ═════════════════════════════════════════════════════════════════════════════
    
    name = fields.Char(
        string='Nombre / Razón social',
        required=True,
    )

    installer_type = fields.Selection(
        selection=[
            ('person', 'Persona / Instalador individual'),
            ('company', 'Empresa subcontratista'),
        ],
        string='Tipo',
        required=True,
        default='person',
    )

    manager_name = fields.Char(
        string='Encargado responsable',
        help='Para empresas: nombre del responsable',
    )

    phone = fields.Char(
        string='Teléfono / WhatsApp',
    )

    state = fields.Selection(
        selection=[
            ('active', 'Activo'),
            ('inactive', 'Inactivo'),
        ],
        string='Estado',
        default='active',
    )

    active = fields.Boolean(
        default=True,
    )

    notes = fields.Html(
        string='Notas',
    )

    # ═════════════════════════════════════════════════════════════════════════════
    # Relations
    # ═════════════════════════════════════════════════════════════════════════════

    work_order_ids = fields.One2many(
        comodel_name='wigo.ftth.work.order',
        inverse_name='installer_id',
        string='Órdenes asignadas',
    )

    work_order_count = fields.Integer(
        string='OTs',
        compute='_compute_work_order_count',
    )

    # ═════════════════════════════════════════════════════════════════════════════
    # Compute Methods
    # ═════════════════════════════════════════════════════════════════════════════

    @api.depends('work_order_ids')
    def _compute_work_order_count(self):
        """Compute number of work orders assigned to installer."""
        for record in self:
            record.work_order_count = len(record.work_order_ids)