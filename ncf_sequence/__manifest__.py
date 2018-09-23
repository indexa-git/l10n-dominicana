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
    'name': "NCF Sequence",
    'version': '11.0.1.0.0',
    'summary': u"""
        Este módulo extiende la funcionalidad de NCF Manager,
        para realizar la configuración y mantenimiento de las secuencias de NCF.
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
    'depends': ['ncf_manager'],

    'data': [
        # 'security/ir.model.access.csv',
        # 'date/ncf_sequence_data.xml',
        'views/ncf_registry_view.xml',
    ],
    'qweb': [
    ]
}
