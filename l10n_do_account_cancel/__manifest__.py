# -*- coding: utf-8 -*-
{
    'name': "l10n_do Cancel Journal Entries",

    'summary': """
        Implementa cancelación de facturas fiscales""",

    'author': "Indexa",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_do_accounting',
                'account_cancel'],

    # always loaded
    'data': [
        'wizard/account_invoice_cancel_views.xml',
        'views/account_invoice_views.xml',
    ],
    'auto_install': True,
}
