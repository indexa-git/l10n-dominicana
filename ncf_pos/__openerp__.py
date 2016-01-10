# -*- coding: utf-8 -*-
{
    'name': "ncf_pos",

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
    'depends': ['base', 'point_of_sale', 'ncf_manager'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_order_cancel_view.xml',
        'wizard/pos_order_refund_view.xml',
        'views.xml',
        'templates.xml',
        'pos_manager/pos_manager_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'qweb': ['static/src/xml/pos.xml']
}
