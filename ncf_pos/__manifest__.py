# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2017 Raúl Ovalle <rovalle@guavana.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
# © 2018 Jefferson Benzan <jbenzan@gruponeotec.com>

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
    'name': "NCF POS",

    'summary': """
        Incorpora funcionalidades de facturación con NCF al POS
        """,

    'author': "Marcos SRL, "
              "iterativo SRL, "
              "Grupo Neotec SRL",
    'category': 'Localization',
    'version': '11.0.0.2.0',

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
