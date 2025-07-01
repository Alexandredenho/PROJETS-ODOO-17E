{
    'name': 'Analytique de caisse externe',
    'version': '1.0',
    'description': 'Ajouter la comptabilité analytique à la caisse externe',
    'summary': 'Ajouter la comptabilité analytique à la caisse externe',
    'author': 'Thomas ATCHA',
    'license': 'LGPL-3',
    'category': 'Tools',
    'depends': [
        'base','th_caisse_externe','analytic'
    ],
    'data': [
        'views/caisse_views.xml',
    ],
    'auto_install': False,
    'application': False,
}