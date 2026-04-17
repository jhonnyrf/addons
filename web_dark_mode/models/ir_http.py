from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def color_scheme(self):
        scheme = request.httprequest.cookies.get("color_scheme")
        if scheme not in ("dark", "light"):
            scheme = None

        user = request.env.user
        if not user or user._is_public():
            return scheme or "light"

        device_dependent = getattr(user, "dark_mode_device_dependent", False)
        if device_dependent:
            return scheme or "light"

        return "dark" if getattr(user, "dark_mode", False) else "light"

    @classmethod
    def _set_color_scheme(cls, response):
        scheme = request.httprequest.cookies.get("color_scheme")
        user = request.env.user
        user_scheme = "dark" if getattr(user, "dark_mode", None) else "light"
        device_dependent = getattr(user, "dark_mode_device_dependent", None)
        if (not device_dependent) and scheme != user_scheme:
            response.set_cookie("color_scheme", user_scheme)

    @classmethod
    def _post_dispatch(cls, response):
        cls._set_color_scheme(response)
        return super()._post_dispatch(response)
