# -*- coding: utf-8 -*-
from odoo import http

# class L10nDoAccounting(http.Controller):
#     @http.route('/l10n_do_accounting/l10n_do_accounting/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_do_accounting/l10n_do_accounting/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_do_accounting.listing', {
#             'root': '/l10n_do_accounting/l10n_do_accounting',
#             'objects': http.request.env['l10n_do_accounting.l10n_do_accounting'].search([]),
#         })

#     @http.route('/l10n_do_accounting/l10n_do_accounting/objects/<model("l10n_do_accounting.l10n_do_accounting"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_do_accounting.object', {
#             'object': obj
#         })