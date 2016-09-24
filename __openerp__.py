# -*- coding: utf-8 -*-

########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################


{
    'name': "Comprobantes fiscales RD",

    'summary': """
        Localizacion Para Republica Dominicana
        Implementacin de numeros de comprobantes fiscales
        """,

    'description': """
        Permite administrar y configurar comprobantes fiscales ademas de generara los reportes
        606,607,608 y 609
    """,

    'author': "Marcos Organizador de Negocios SRL - Write by Eneldo Serrata",
    'website': "http://marcos.do",

    'category': 'Localization',
    'version': '2.0',


    'depends': ['base','account', 'account_accountant', 'l10n_do','rnc_validation'],

    'data': [
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/shop_view.xml',
        'views/partner_view.xml',
        'views/account_view.xml',
        'views/account_invoice_view.xml',
        'views/dgii_purchase_view.xml',
        'views/dgii_sale_view.xml',
        'views/dgii_cancel_view.xml',
        'views/dgii_exterior_view.xml',
        'views/account_invoice_state_view.xml',
        'views/account_move_view.xml',
        'wizard/account_invoice_refund_view.xml',
        'wizard/invoice_currency_change_wizard_view.xml',
        'data/setup_ncf.xml'
    ],
    "qweb": ['static/src/xml/base.xml'],
    'demo': [],
    'images': 'static/description/main.png',
    "price": 2000,
    'currency': 'EUR',
    'license': "Other proprietary"

}