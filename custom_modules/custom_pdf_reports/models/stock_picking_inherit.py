from odoo import fields, models, api


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    driver_id = fields.Many2one(
        comodel_name='res.partner',
        string='Chauffeur',
    )

    picking_controller_id = fields.Many2one(
            comodel_name='res.partner',
            string='Contôleur',
        )

    company_owner_id = fields.Many2one(
        comodel_name='hr.employee',
        string='PDG',
    )

    picking_manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Magasinier',
    )

    def do_print_picking(self):
        self.write({'printed': True})
        return self.env.ref('custom_pdf_reports.custom_action_report_delivery').report_action(self)
