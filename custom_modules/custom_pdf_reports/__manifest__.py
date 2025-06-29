{
    'name': 'Personnalisation des rapports PDF',
    'version': '17.0.1.0.0',
    'category': 'Ventes, Achats, inventaire,comptabilité',
    'summary': 'Ce module permet de personnaliser les rapports pdf des modules Achats, ventes, inventaire et comptabilité',
    'depends': ['base', 'hr', 'stock', 'sale', 'purchase', 'account'],
    "author": "ALEXANDRE KOUA",
    "maintainer": "ALEXANDRE KOUA",
    "contributors": [
        "Alexandre Koua",
        "saintkoffakk@gmail.com",
    ],
    'data': [
        # Report
        'report/custom_purchase_order_template.xml',
        'report/custom_report_stock_reception_template.xml',
        'report/custom_all_reports.xml',
        'report/custom_account_payment_template.xml',
        'report/custom_sale_order_template.xml',

        # Views
        'views/custom_purchase_order_views.xml',
        'views/custom_stock_picking_views.xml',
        'views/custom_account_payment_views.xml',
        'views/custom_sale_order_views.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    'license': 'LGPL-3',
}
