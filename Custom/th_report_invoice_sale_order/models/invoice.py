from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

class ResCompany(models.Model):

    _inherit = 'res.company'

    company_name = fields.Char(string="Nom de la socité")
    numeroimpex = fields.Char(string="N° Imp/Ex :")
    description = fields.Char(string="Description")
    id_nat = fields.Char(string="ID Nat")
    rccm = fields.Char(string="RCCM")
    nif = fields.Char(string="NIF")


class ResPartner(models.Model):

    _inherit = 'res.partner'

    ref = fields.Char(string="N° Référence client", copy=False, default='Nouveau')
    jounral_sale_id = fields.Many2one(
        'account.journal',
        string='Journal de vente par défaut',
        
        domain=[('type','=','sale')]
        
        )
    jounral_purchase_id = fields.Many2one(
        'account.journal',
        string='Journal d\'achat par défaut',
        domain=[('type','=','purchase')]
        )
    stock_location_id = fields.Many2one(
    'stock.warehouse',
    string='Entrepôt de livraison',
    )
    @api.model
    def create(self, vals):
        result = None
        if vals.get('ref', 'Nouveau') == 'Nouveau':
            vals['ref'] = self.env['ir.sequence'].next_by_code(
				'res.partner') or 'Nouveau'
            result = super(ResPartner, self).create(vals)
        return result


class AccountMove(models.Model):

    _inherit = 'account.move'

    stock_picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string='Bons de commande',
    )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.type == 'out_invoice':
                if rec.partner_id.jounral_sale_id :
                    rec.journal_id = rec.partner_id.jounral_sale_id.id

            if rec.type == 'out_invoice':
                if rec.partner_id.jounral_purchase_id:
                    rec.journal_id = rec.partner_id.jounral_purchase_id.id