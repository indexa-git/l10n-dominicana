# -*- coding: utf-8 -*-
{
    'name': "Comprobantes fiscales RD",

    'summary': """
        Permite administrar y configurar comprobantes fiscales ademas de generara los reportes
        606,607,608 y 609
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': 'Eneldo Serrata - Marcos Organizador de Negocios, SRL.',
    'website': "http://marcos.do",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account', 'account_accountant', 'l10n_do'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'views/shop_view.xml',
        'views/account_view.xml',
        'views/account_invoice_view.xml',
        'views/dgii_purchase_view.xml',
        'views/dgii_sale_view.xml',
        'views/dgii_cancel_view.xml',
        'views/dgii_exterior_view.xml',
        'views/account_invoice_state_view.xml',
        'data/setup_ncf.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images': 'static/description/main.png',
    "price": 1500,
    'currency': 'EUR'
}