# from odoo import http


# class ContactosExt(http.Controller):
#     @http.route('/contactos_ext/contactos_ext', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contactos_ext/contactos_ext/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('contactos_ext.listing', {
#             'root': '/contactos_ext/contactos_ext',
#             'objects': http.request.env['contactos_ext.contactos_ext'].search([]),
#         })

#     @http.route('/contactos_ext/contactos_ext/objects/<model("contactos_ext.contactos_ext"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contactos_ext.object', {
#             'object': obj
#         })

