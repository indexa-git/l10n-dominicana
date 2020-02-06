{
    'name': "Fiscal Accounting (Rep. Dominicana)",
    'summary': """
        Este módulo implementa la administración y gestión de los números de
         comprobantes fiscales para el cumplimento de la norma 06-18 de la
         Dirección de Impuestos Internos en la República Dominicana.""",
    'author': "iterativo LLC, " "Indexa",
    'category': 'Localization',
    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'version': "13.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['l10n_latam_invoice_document',
                'l10n_do',
                ],
    # always loaded
    'data': [
        # 'security/res_groups.xml',
        'data/l10n_latam.document.type.csv',
        'wizard/account_move_reversal_views.xml',
        'wizard/account_move_cancel_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/account_dgii_menuitem.xml',
        'views/account_journal_views.xml',
        'views/l10n_latam_document_type_views.xml',
        'views/report_invoice.xml'
    ],
    'qweb': [
        # "static/src/xml/fiscal_sequence_warning_template.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/res_partner_demo.xml',
        # 'demo/account_fiscal_sequence_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
