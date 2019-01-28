{
    'name': "Formatos Envio DGII",

    'summary': """
        Localizacion Para Republica Dominicana
        Implementacion de formatos de envio de documentos DGII
        """,

    'description': """
        Permite generar los reportes 606,607,608 y 609
    """,

    'author': "Angstrom Mena",
    'website': "",

    'category': 'Localization',
    'version': '2.0',

    'depends': ['base', 'account', 'ncf_manager'],

    'data': [
        "views/dgii_purchase_view.xml"
    ],
    'license': "Other proprietary"
}
