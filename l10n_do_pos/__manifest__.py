
{
    'name': "Fiscal POS (Rep. Dominicana)",

    'summary': """Incorpora funcionalidades de facturación con NCF al POS.""",

    'author': "Xmarts, "
              "Indexa, "
              "Iterativo SRL",

    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '13.0.0.0.1',
    'depends': [
        'base',
        'point_of_sale',
        'l10n_do_accounting',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        # 'views/account_journal_views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/posticket.xml',
    ],
    'demo': [

    ],
    'installable': True,
}
