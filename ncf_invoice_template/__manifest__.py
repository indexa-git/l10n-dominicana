# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 José López <jlopez@indexa.do>

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
    'name': "NCF Invoice Template",
    'summary': """
    Este modulo sobre escribe el formato de las facturas para adaptarlo a la
    Norma General 06-2018 de la DGII.
    """,
    'description': """
    Adapta el formato de las facturas a la Norma General 06-2018 de la DGII.
    """,
    'author': "Yasmany Castillo, "
              "iterativo SRL",
    'category': 'Localization',
    'version': '11.0.2.0.0',
    'depends': ['web', 'ncf_manager'],

    'data': [
        'report/report_invoice.xml',
    ],
}
