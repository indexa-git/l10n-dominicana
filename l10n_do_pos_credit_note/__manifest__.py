{
    'name': "Fiscal POS Credit Notes (Rep. Dominicana)",
    'summary': """Incorpora funcionalidades de notas de credito con NCF al POS.""",
    'author': "Xmarts",
    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '13.0.0.0.1',
    'depends': [
        'base',
        'point_of_sale',
        'l10n_do_pos',
        'pos_orders_history_return',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        # 'views/account_journal_views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/posticket.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
}
