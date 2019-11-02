{
    'name': "Fiscal Accounting (Rep. Dominicana)",

    'summary': """
        Este módulo implementa la administración y gestión de los números de
         comprobantes fiscales para el cumplimento de la norma 06-18 de la
         Dirección de Impuestos Internos en la República Dominicana.""",

    'author': "Guavana, "
              "Indexa, "
              "Iterativo SRL",

    'license': 'LGPL-3',
    'website': "https://github.com/odoo-dominicana",
    'category': 'Localization',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'l10n_do',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/ir_cron_data.xml',
        'data/account_fiscal_type_data.xml',
        'views/account_fiscal_sequence_views.xml',
        'wizard/account_fiscal_sequence_validate_wizard_views.xml',
        'views/report_templates.xml',
        'data/report_layout_data.xml',
        'views/account_report.xml',
        'views/report_invoice.xml',
        'wizard/account_invoice_refund_views.xml',
        'data/mail_template_data.xml',
        'views/account_invoice_views.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml',
        'views/assets.xml'
    ],
    'qweb': [
        "static/src/xml/fiscal_sequence_warning_template.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/res_partner_demo.xml',
        'demo/account_fiscal_sequence_demo.xml',
    ],
}
