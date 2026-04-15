# from odoo import http


# class WigoCrm(http.Controller):
#     @http.route('/wigo_crm/wigo_crm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wigo_crm/wigo_crm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wigo_crm.listing', {
#             'root': '/wigo_crm/wigo_crm',
#             'objects': http.request.env['wigo_crm.wigo_crm'].search([]),
#         })

#     @http.route('/wigo_crm/wigo_crm/objects/<model("wigo_crm.wigo_crm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wigo_crm.object', {
#             'object': obj
#         })

