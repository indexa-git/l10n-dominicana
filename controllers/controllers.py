# -*- coding: utf-8 -*-
from odoo import http

# class NcfManager(http.Controller):
#     @http.route('/ncf_manager/ncf_manager/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_manager/ncf_manager/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_manager.listing', {
#             'root': '/ncf_manager/ncf_manager',
#             'objects': http.request.env['ncf_manager.ncf_manager'].search([]),
#         })

#     @http.route('/ncf_manager/ncf_manager/objects/<model("ncf_manager.ncf_manager"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_manager.object', {
#             'object': obj
#         })