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
    'depends': ['account', 'marcos_api_tools', 'l10n_do', 'sale',
                'account_cancel'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ncf_manager_security.xml',
        'wizard/account_invoice_cancel_view.xml',
        'wizard/update_rate_wizard_view.xml',
        'wizard/account_invoice_refund.xml',
        'views/shop_view.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/res_currency_view.xml',
        'data/sequences.xml',
        'views/templates.xml',
        'views/res_view.xml',
        'views/dgii_report_view.xml',
        'data/setup_ncf.xml'
    ],
}
