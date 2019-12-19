{
    'name': 'l10n do external valdiation RNC',
    'version': '12.0.0.0.0',
    'summary': 'Validate rnc and cedula from indexa api',
    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': '',
    'author': 'Guavana,'
              'Indexa,'
              'Iterativo',
    'website': 'https://github.com/odoo-dominicana',
    'license': '',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_setup',
    ],
    # always loaded
    'data': [
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
}
