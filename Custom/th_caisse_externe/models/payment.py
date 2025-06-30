from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from datetime import datetime


class IrSequence(models.Model):

    _inherit = 'ir.sequence'

    type_cassie_id = fields.Many2one(
        'type.caisse',
        string='Type de caisse',
    )

class AccountMove(models.Model):

    _inherit = 'account.move'

    caisse_id = fields.Many2one(
        'account.caisse',
        string='caisse',
        check_company=True,ondelete='cascade'
    )

    categorie_id = fields.Many2one(
        'categorie.operation',
        string='categorie', check_company=True, ondelete='cascade'
    )

    caisse_line_id = fields.Many2one(
        'account.caisse.line',
        string='Ligne de caisse externe',
        ondelete='cascade'
    )
    
class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    caisse_id = fields.Many2one(
        'account.caisse',
        string='caisse',check_company=True, ondelete='cascade'
        )

    categorie_id = fields.Many2one(
        'categorie.operation',
        string='categorie',check_company=True, ondelete='cascade'
    )

    caisse_line_id = fields.Many2one(
        'account.caisse.line',
        string='Ligne de caisse externe', ondelete='cascade'
    )


class ModelBilletage(models.Model):

    _name = 'modele.billetage'
    _description = 'Modele de billetage'
    _check_company_auto = True

    name = fields.Char(string="Nom")
    line_ids = fields.One2many('modele.billetage.line', 'modele_id', check_company=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env.company.id
        
    )

    
class ModeleBilletageLine(models.Model):

    _name = 'modele.billetage.line'
    _description = 'Ligne de modele de billetage'
    _check_company_auto = True

    nombre = fields.Float(string="Nombre de billet/pièce")
    valeur = fields.Float(string="Valeur")
    montant = fields.Float(string="Montant")

    modele_id = fields.Many2one(
        'modele.billetage',
        string='Model de billetage', check_company=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env.company.id
    )

    @api.onchange('nombre','valeur')
    def onchange_nombre_valeur(self):
        for rec in self:
            rec.montant = rec.nombre * rec.valeur
