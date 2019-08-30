{
    'name': "Stock Import Wizard",

    'summary': """
        Este modulo permite copiar desde un excel o txt un invetario para importarlo en Odoo 
     """,
    'description': """
        
    """,

    'author': "Eneldo Serrata",
    'website': "https://marcos.do",

    'category': 'Hidden',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'wizard/inventory_import_view.xml',
    ],
}
