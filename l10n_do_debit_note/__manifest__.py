{
    'name': "Dominican Debit Notes",
    'summary': """
    Adds Dominican Republic Debit Notes features
    """,
    'author': "iterativo LLC, " "Indexa",
    'category': 'Localization',
    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'version': "13.0.1.0.0",
    'depends': [
        'account_debit_note',
        'l10n_do_accounting',
    ],
    'data': [
        'views/account_views.xml',
        'wizard/account_debit_note_views.xml',
    ],
    'auto_install': True,
    'installable': True,
}
