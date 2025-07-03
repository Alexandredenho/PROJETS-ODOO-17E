from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from datetime import datetime


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    caisse_id = fields.Many2one(
        'account.caisse',
        ondelete='cascade',
        string='Caisse', check_company=True
    )
    caisse_line_id = fields.Many2one(
        'account.caisse.line',
        string='Ligne de caisse', ondelete='cascade',
        check_company=True
    )

    @api.onchange('journal_id')
    def onchange_caisse_id(self):
        return {'domain':{'caisse_id':[
            ('account_journal_id','=',self.journal_id.id),
            ('state','=', 'draft')
        ]}}


class AccountMove(models.Model):

    _inherit = 'account.move'

    caisse_id = fields.Many2one(
        comodel_name='account.caisse',
        string='caisse',
        check_company=True,
        ondelete='cascade'
    )

    categorie_id = fields.Many2one(
        comodel_name='categorie.operation',
        string='categorie',
        check_company=True,
        ondelete='cascade'
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


class ResPartner(models.Model):

    _inherit = 'res.partner'

    compte_salarie_id = fields.Many2one(
        'account.account',
        string='Compte salarié',
        )
    compte_autre_id = fields.Many2one(
        'account.account',
        string='Autre compte',
    )


class DiffenceChange(models.Model):

    _name = 'diffence.change'
    _check_company_auto = True
    _description = 'Différence de change'

    ref = fields.Char(string='Référence')
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True,
        ondelete='restrict',
        default=lambda self: self.env.company
    )
