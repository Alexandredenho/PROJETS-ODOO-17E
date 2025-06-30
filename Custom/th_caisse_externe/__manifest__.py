{
    'name': 'Caisse externe',
    'version': '17.0.1.0.0',
    'description': 'Gestion de caisse externe à la comptabilité',
    'summary': 'Gestion de caisse externe à la comptabilité',
    'author': 'KOUA Alexandre',
    "maintainer": "ALEXANDRE KOUA",
    "contributors": [
        "Alexandre Koua",
        "kouaalexandrepro18@gmail.com",
    ],
    'category': 'Tools',

    'depends': [
        'base', 'account', 'mail'
    ],
    'data': [
        # security
        'security/security.xml',
        'security/ir.model.access.csv',

        # data
        'data/data.xml',

        # views
        'views/dashboard.xml',
        'views/account_move.xml',
        'views/caisse_views.xml',
        'wizards/justifier.xml',
        'views/caisse_line_views.xml',
        'views/sortie_attente_views.xml',
        'views/accounting.xml',
        'views/payment_views.xml',
        'views/settings.xml',
        'views/res_partner_views.xml',

        # reports
        'reports/detail_report.xml',
        'reports/cash_report_view.xml',
        'reports/cash_detail_report_veiw.xml',
        'reports/th_report_billetage.xml',

        # wizards

        'wizards/billetage.xml',
        'wizards/cash_report_view.xml',
    ],

    "installable": True,
    "auto_install": False,
    "application": False,
    'license': 'LGPL-3',
}
