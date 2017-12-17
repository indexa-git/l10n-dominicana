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
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['ncf_manager', 'point_of_sale', 'pos_order_return',
                'pos_orders'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_view.xml',
        'views/res_config.xml',
        'views/pos_sesion_view.xml',
        'views/pos_config_view.xml',
        'data/data.xml',
        'views/templates.xml',

    ],
    'qweb': [
        'static/src/xml/ncf_pos.xml',
        'static/src/xml/pos.xml',
    ],
}
