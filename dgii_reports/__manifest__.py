# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Eneldo Serrata <eneldo@marcos.do>

{
    'name': "Declaraciones DGII",

    'summary': """
        Este módulo extiende las funcionalidades del ncf_manager,
        integrando los reportes de declaraciones fiscales
        migrado de la version 12 por MERPLUS 23/10/2021""",

    'author': "Indexa, SRL, "
              "iterativo SRL",
    'license': 'LGPL-3',
    'category': 'Accounting',
    'version': '15.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_do_accounting_plus'],

    # always loaded
    'data': [
        'data/invoice_service_type_detail_data.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/res_partner_views.xml',
        'views/account_account_views.xml',
        'views/account_invoice_views.xml',
        'views/dgii_report_views.xml',
        'views/menu.xml',
        # 'views/dgii_report_templates.xml',
        'wizard/dgii_report_regenerate_wizard_views.xml',
    ],
}
