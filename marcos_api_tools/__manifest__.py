# -*- coding: utf-8 -*-
{
    'name': "Marcos API",

    'summary': """
        Integracion para evaluación de NCF, RNC y consultas de tasas de cambio en Bancos Dominicanos.
        """,

    'description': """
        Marcos ofrese una Api (http://api.marcos.do/) de forma gratuita que permite validacion de con la DGII de NCF y RNC ademas de consultas de tasas de cmabio en los banco Dominicanos incluyendo Las tasas publicadas por el Banco Central.
    """,

    'author': "Marcos Organizador de Negocios SRL - Write by Eneldo Serrata",
    'website': "http://marcos.do",

    'category': 'Localization',
    'version': '10.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
    ],
}
