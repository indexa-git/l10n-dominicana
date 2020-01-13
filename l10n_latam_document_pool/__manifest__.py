{
    "name": "l10n_latam_document_pool",
    "summary": """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    "description": """
        Long description of module's purpose
    """,
    "author": "My Company",
    "website": "http://www.yourcompany.com",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["l10n_do_accounting"],
    "data": [
        'security/ir.model.access.csv',
        "data/ir_cron_data.xml",
        "wizard/l10n_latam_document_pool_validate_wizard_views.xml",
        "views/l10n_latam_document_pool_views.xml",
    ],
}
