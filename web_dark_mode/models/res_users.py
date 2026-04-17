from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    dark_mode = fields.Boolean()
    dark_mode_device_dependent = fields.Boolean("Device Dependent Dark Mode")

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "dark_mode_device_dependent",
            "dark_mode",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "dark_mode_device_dependent",
            "dark_mode",
        ]

    def set_dark_mode_preference(self, enabled):
        self.ensure_one()
        self.sudo().write({"dark_mode": bool(enabled)})
        return bool(self.dark_mode)

    def get_dark_mode_preference(self):
        self.ensure_one()
        return bool(self.sudo().dark_mode)
