# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
#             Manuel Marquez <buzondemam@gmail.com>

# This file is part of NCF Purchase.

# NCF Purchase is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Purchase is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

{
    'name': "NCF Purchase",
    'version': '11.0.0.1.0',
    'summary': u"""
    Add new field "Purchase Journal" in suppliers if this field is set
    the invoices generated for these suppliers take this journal by default.
    """,
    'author': "Marcos Organizador de Negocios SRL, "
              "iterativo SRL, "
              "Odoo Dominicana (ODOM) ",
    'category': 'Localization',

    'depends': ['ncf_manager', 'purchase'],

    'data': [
        'views/res_partner_views.xml',
    ],
}
