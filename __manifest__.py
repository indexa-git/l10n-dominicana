# -*- coding: utf-8 -*-
{
    'name': "ncf_manager",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_invoice_refund_link','account_invoice_change_currency','web_sheet_full_width'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/shop_view.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'data/setup_ncf.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}