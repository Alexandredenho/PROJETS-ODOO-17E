from odoo import fields, models, api

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    purchase_manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Responsable des achats',
    )

    company_owner_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Directeur Général',
    )
    


