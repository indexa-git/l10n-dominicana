{
    'name': "l10n_do Cancel Journal Entries",

    'summary': """
        Implementa cancelación de facturas fiscales""",

    'author': "Indexa",
    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '13.0.1.0.0',

    'depends': ['l10n_do_accounting'],

    'data': [
        'wizard/account_move_cancel_views.xml',
        'views/account_move_views.xml',
    ],
    'auto_install': True,
    'installable': True,
}
