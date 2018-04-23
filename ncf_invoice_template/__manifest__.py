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
    'author': "Yasmany Castillo",
    'website': "",
    'category': 'Category Hidden',
    'version': '0.1',
    'depends': ['web', 'account'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/report_paperformat.xml',
        'report/report_invoice.xml',
        'report/report_templates.xml',
    ],
}
