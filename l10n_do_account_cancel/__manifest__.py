{
    'name': "l10n_do Cancel Journal Entries",

    'summary': """
        Implementa cancelación de facturas fiscales""",

    'author': "Indexa",

    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '12.0.1.0.0',

    'depends': ['l10n_do_accounting',
                'account_cancel'],

    'data': [
        'wizard/account_invoice_cancel_views.xml',
        'views/account_invoice_views.xml',
    ],
    'auto_install': True,
}
