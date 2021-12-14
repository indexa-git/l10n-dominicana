{
    "name": "Dominican Debit Notes",
    "summary": """
    Adds Dominican Republic Debit Notes features
    """,
    "author": "iterativo LLC, " "Indexa",
    "category": "Localization",
    "license": "LGPL-3",
    "website": "https://github.com/odoo-dominicana",
    "version": "13.0.1.3.3",
    "depends": ["account_debit_note", "l10n_do_accounting"],
    "data": [
        "security/res_groups.xml",
        "views/account_views.xml",
        "wizard/account_debit_note_views.xml",
    ],
    "auto_install": True,
    "installable": True,
    "post_init_hook": "post_init_hook",
}
