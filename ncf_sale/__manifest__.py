# © 2018 Yasmany Castillo <yasmany003@gmail.com>

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
    'name': "NCF Sale",
    'version': '11.0.0.1.0',
    'summary': """
        Este módulo extiende la funcionalidad de NCF Manager hacia ventas,
        para realizar algunas validaciones antes de crear la factura.
    """,
    'author': "Yasmany Castillo",
    'category': 'Localization',

    'external_dependencies': {
        'python': [
            'stdnum.do',
        ],
    },

    # any module necessary for this one to work correctly
    'depends': ['ncf_manager', 'sale_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',

    ],
    'qweb': [
    ]
}
