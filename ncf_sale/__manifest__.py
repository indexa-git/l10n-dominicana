# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
# © 2017-2018 Neotec SRL. (https://neotec.do/)
#             Yasmany Castillo <yasmany003@gmail.com>


# This file is part of NCF Manager.

# NCF Sale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Sale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Sale.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

{
    'name': "NCF Sale",
    'version': '11.0.1.0.0',
    'summary': u"""
        Este módulo extiende la funcionalidad de NCF Manager hacia ventas,
        para realizar algunas validaciones antes de crear la factura.
    """,
    'author': "Marcos Organizador de Negocios SRL, "
              "iterativo SRL, "
              "Neotec SRL, "
              "Odoo Dominicana (ODOM) ",
    'category': 'Localization',

    'external_dependencies': {
        'python': [
            'stdnum.do',
        ],
    },

    # any module necessary for this one to work correctly
    'depends': ['ncf_manager', 'sale',],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',

    ],
    'qweb': [
    ]
}
