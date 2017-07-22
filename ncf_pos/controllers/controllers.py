# -*- coding: utf-8 -*-
from odoo import http

# class NcfPos(http.Controller):
#     @http.route('/ncf_pos/ncf_pos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ncf_pos/ncf_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ncf_pos.listing', {
#             'root': '/ncf_pos/ncf_pos',
#             'objects': http.request.env['ncf_pos.ncf_pos'].search([]),
#         })

#     @http.route('/ncf_pos/ncf_pos/objects/<model("ncf_pos.ncf_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ncf_pos.object', {
#             'object': obj
#         })