from odoo import fields, models, api


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    company_owner_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Directeur Général',
    )

    sales_manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Responsable des ventes',
    )

