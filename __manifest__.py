# -*- coding: utf-8 -*-
{
    'name': "Declaraciones DGII",

    'summary': """
        Este módulo extiende las funcionalidades del ncf_manager,
        integrando los reportes de declaraciones fiscales""",

    'author': "Marcos Organizador de Negocios SRL, "
              "iterativo SRL, "
              "Neotec, "
              "Odoo Dominicana (ODOM)",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account_invoicing',
                'ncf_manager'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/account_account_views.xml',
        'views/account_invoice_views.xml',
        'views/dgii_report_views.xml',
        'views/dgii_report_templates.xml',
    ],
}
