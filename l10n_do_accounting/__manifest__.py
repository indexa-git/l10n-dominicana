{
    'name': "Fiscal Accounting (Rep. Dominicana)",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/account_fiscal_type_data.xml',
        'views/account_fiscal_sequence_views.xml',
        'wizard/account_fiscal_sequence_validate_wizard_views.xml',
        'views/account_invoice_views.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
