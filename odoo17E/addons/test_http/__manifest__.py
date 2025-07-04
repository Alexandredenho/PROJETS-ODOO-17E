# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Test HTTP',
    'version': '1.0',
    'category': 'Hidden/Tests',
    'description': """A module to test HTTP""",
    'depends': ['base', 'web', 'web_tour'],
    'installable': True,
    'data': [
        'data.xml',
        'ir.model.access.csv',
        'account_caisse_line_inherit_views.xml'
    ],
    'license': 'LGPL-3',
}
