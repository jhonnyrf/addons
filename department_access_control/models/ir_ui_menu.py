# -*- coding: utf-8 -*-
from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def name_get(self):
        # El autocomplete del many2one usa name_get; devolvemos la ruta completa
        # para que la selección muestre el mismo texto jerárquico que complete_name.
        return [(menu.id, menu.complete_name or menu.name) for menu in self]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if name:
            # La búsqueda se mantiene sobre el nombre base; la presentación la da name_get.
            menus = self.search(args + [('name', operator, name)], limit=limit)
            return menus.name_get()
        return self.search(args, limit=limit).name_get()

    def _department_access_employee(self):
        user = self.env.user
        candidates = (user.employee_id | user.employee_ids).filtered(
            lambda e: e.use_department_access and e.department_id and e.department_id.restrict_access
        )
        if not candidates:
            return False

        current_company = self.env.company
        company_match = candidates.filtered(lambda e: e.company_id == current_company)
        return (company_match or candidates)[:1]

    def _department_access_visible_menu_ids(self):
        employee = self._department_access_employee()
        if not employee:
            return False

        employee = employee[0]

        menu_ids = employee.get_effective_menu_ids()
        if not menu_ids:
            return frozenset()

        return frozenset(menu_ids)

    def _visible_menu_ids(self, debug=False):
        visible_ids = super()._visible_menu_ids(debug=debug)
        allowed_ids = self._department_access_visible_menu_ids()

        if allowed_ids is False:
            return visible_ids

        return frozenset(visible_ids & allowed_ids)

    def load_web_menus(self, debug=False):
        menus = super().load_web_menus(debug=debug)
        allowed_ids = self._department_access_visible_menu_ids()

        if allowed_ids is False:
            return menus

        allowed_ids = set(allowed_ids)
        filtered = {}

        for key, menu in menus.items():
            if key == 'root' or key in allowed_ids:
                filtered[key] = dict(menu)

        for key, menu in filtered.items():
            children = menu.get('children') or []
            menu['children'] = [child_id for child_id in children if child_id in filtered]

        return filtered