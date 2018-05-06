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
    'name': "NCF POS",

    'summary': u"""
        Incorpora funcionalidades de facturación con NCF al POS
        """,

    'author': "Marcos Organizador de Negocios SRL, "
              "iterativo SRL, "
              "Odoo Dominicana (ODOM) ",
    'category': 'Localization',
    'version': '10.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['ncf_manager', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/pos_config.xml',
        'views/pos_view.xml',
        'data/data.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/ncf_ticket.xml',
    ]
}