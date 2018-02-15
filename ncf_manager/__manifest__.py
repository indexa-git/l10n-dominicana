# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

{
    'name': "Gestor de Comprobantes Fiscales (NCF Manager)",
    'version': '11.0.1.0.0',
    'summary': """
        Módulo para la administración y configuración de los NCF autorizados
         a la empresa por la DGII.
    """,

    'description': """
        Este módulo implementa la administración y gestión de los números de
         comprobantes fiscales para el cumplimento de la norma 06-18 de la
         Dirección de Impuestos Internos en la República Dominicana.
    """,

    'author': "Marcos Organizador de Negocios SRL, "
              "iterativo SRL, "
              "Odoo Dominicana (ODOM) ",
    'category': 'Localization',

    # any module necessary for this one to work correctly
    'depends': ['account_invoicing', 'l10n_do', 'account_cancel'],

    'data': [
        'security/ir.model.access.csv',
        'security/ncf_manager_security.xml',
        'wizard/account_invoice_cancel_view.xml',
        'wizard/update_rate_wizard_view.xml',
        'wizard/account_invoice_refund.xml',
        'views/shop_view.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/res_currency_view.xml',
        'data/sequences.xml',
        'views/res_view.xml',
        'views/templates.xml',
        'data/setup_ncf.xml'
    ],
}
