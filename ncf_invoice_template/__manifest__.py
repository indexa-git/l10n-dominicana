# -*- coding: utf-8 -*-
{
    'name': "NCF Invoice Template",
    'summary': """
    Este modulo sobre escribe el formato de las facturas para adaptarlo a la
    Norma General 06-2018 de la DGII.
    """,
    'description': """
    Adapta el formato de las facturas a la Norma General 06-2018 de la DGII.
    """,
    'author': "Marcos Organizador de Negocios SRL, "
              "iterativo SRL, "
              "Odoo Dominicana (ODOM) ",
    'website': "",
    'category': 'Category Hidden',
    'version': '10.0.1.0.0',
    'depends': ['web',
                'ncf_manager'],
    'data': [
        'report/report_invoice.xml',
    ],
}
