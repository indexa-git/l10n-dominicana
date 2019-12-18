{
    'name': 'l10n do external valdiation RNC',
    'version': '12.0.0.0.0',
    'summary': 'Validate rnc and cedula from indexa api',
    'description': 'Validate rnc and cedula from indexa api',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'author': 'Guavana,'
              'Indexa,'
              'Iterativo',
    'website': 'https://github.com/odoo-dominicana',
    'license': '',
    # any module necessary for this one to work correctly
    'depends': [
        'base'
    ],
    # always loaded
    'data': [
        'views/res_partner_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
}