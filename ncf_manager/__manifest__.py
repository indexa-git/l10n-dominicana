# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 José López <jlopez@indexa.do>
# © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Andrés Rodríguez <andres@iterativo.do>

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
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

{
    'name': "Gestor de Comprobantes Fiscales (NCF Manager)",
    'version': '12.0.1.1.0',
    'summary': """
        Este módulo implementa la administración y gestión de los números de
         comprobantes fiscales para el cumplimento de la norma 06-18 de la
         Dirección de Impuestos Internos en la República Dominicana.
    """,
    'author': "Marcos SRL, "
              "iterativo SRL",
    'license': 'LGPL-3',
    'category': 'Localization',
    'external_dependencies': {
        'python': ['stdnum.do'],
    },

    # any module necessary for this one to work correctly
    'depends': ['account', 'l10n_do', 'account_cancel'],

    'data': [
        'data/ir_config_parameters.xml',
        'security/ir.model.access.csv',
        'wizard/account_invoice_cancel_view.xml',
        'wizard/account_invoice_refund.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/res_currency_view.xml',
        'views/assets_backend.xml',
        'views/ir_sequence_view.xml',
        'views/res_view.xml',
    ],
    'demo': ['demo/res_partner_demo.xml'],
    'qweb': ['static/src/xml/ncf_manager.xml']
}
