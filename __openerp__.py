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
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/partner_view.xml',
        'views/shop_view.xml',
        'views/account_view.xml',
        'views/account_invoice_view.xml',
        'views/dgii_purchase_view.xml',
        'views/dgii_sale_view.xml',
        'views/dgii_cancel_view.xml',
        'views/dgii_exterior_view.xml',
        'views/account_invoice_state_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}