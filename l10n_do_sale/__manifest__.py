# © 2018 Yasmany Castillo <yasmany003@gmail.com>

{
    'name': "Fiscal Sales (Rep. Dominicana)",

    'summary': """
        This module extends l10n_do_accounting to the Sales module,
        to send required fields to the invoice on creation.
    """,

    'author': "iterativo SRL, "
              "Yasmany Castillo",

    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'l10n_do_accounting',
        'sale'
    ],
    'installable': False,
}
