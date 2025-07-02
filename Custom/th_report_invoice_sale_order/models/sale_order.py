from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        for rec in self:
             if rec.partner_id.stock_location_id:
                rec.warehouse_id = rec.partner_id.stock_location_id.id