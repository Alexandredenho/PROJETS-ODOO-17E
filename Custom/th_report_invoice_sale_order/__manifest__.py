# -*- coding: utf-8 -*-
{
    'name': 'Ajouter des rapports personnalisés',
    'summary': 'Ajouter des rapports personnalisés Module Project',
    'version': '17.0.1.0.0',
    'description': 'Gestion de caisse externe à la comptabilité',
    'author': 'Thomas ATCHA',
    "maintainer": "ALEXANDRE KOUA",
    "contributors": [
        "Alexandre Koua",
        "kouaalexandrepro18@gmail.com",
        "Thomas ATCHA <odootogo@gmail.com>"
    ],

    'category': 'Uncategorized',

    'depends': [
        'base', 'account', 'sale', 'stock',
    ],

    'data': [
        'data/data.xml',
        'views/invoice_view.xml',
        'reports/delivry_report.xml',
        'reports/invoice_report_sans_remise.xml',
        'reports/invoice_report.xml',
        'reports/sale_order_report_sans_remise.xml',
        'reports/sale_order_report.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}
