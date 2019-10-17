{
    'name': "Fiscal POS (Rep. Dominicana)",

    'summary': """Incorpora funcionalidades de facturación con NCF al POS.""",

    'author': "Guavana, "
              "Indexa, "
              "Iterativo SRL",

    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '12.2.0.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'point_of_sale',
        'l10n_do_accounting',
    ],

    # always loaded
    'data': [
        'views/assets.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
        'static/src/xml/posticket.xml'
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
