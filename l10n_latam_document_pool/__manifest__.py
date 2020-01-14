{
    'name': "Latam Documents Pools",
    'summary': """
        This module implements sequence pools for Document types, allowing for fiscal
        scenarios where each Document Type could have more than one sequence available
        """,
    'author': "Indexa",
    'category': 'Localization',
    'license': 'LGPL-3',
    'website': "https://indexa.do/",
    'version': "13.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['l10n_latam_invoice_document',
                ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        "data/ir_cron_data.xml",
        "wizard/l10n_latam_document_pool_validate_wizard_views.xml",
        "views/l10n_latam_document_pool_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
