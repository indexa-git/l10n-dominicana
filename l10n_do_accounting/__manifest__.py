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
    'version': "1.0",
    # any module necessary for this one to work correctly
    'depends': ['l10n_latam_invoice_document', 'l10n_do',],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/res_groups.xml',
        'data/l10n_latam.document.type.csv',
        'views/account_move_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/account_journal_view.xml',
        'views/l10n_latam_document_type_view.xml',
        'views/ir_sequence_view.xml',
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
