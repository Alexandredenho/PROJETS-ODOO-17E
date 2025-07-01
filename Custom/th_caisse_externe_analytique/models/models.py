from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

class AccountCaisseLine(models.Model):

    _inherit = 'account.caisse.line'

    analitic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Compte analytique',
    )
    compte_analytique = fields.Boolean(string="Accepter les comptes analytique", related='categorie_id.compte_analytique')
    analytique_tag_ids = fields.Many2many('account.analytic.tag')

    def poster_operation(self):
        result = super().poster_operation()
        if result:
            for line in result.line_ids:
                if line.debit > 0:
                    line.write({
                        'analytic_account_id' : self.analitic_account_id.id,
                        'analytic_tag_ids' : self.analytique_tag_ids.ids,
                    })
        return result

class CategorieOperation(models.Model):

    _inherit = 'categorie.operation'
    compte_analytique = fields.Boolean(string="Accepter les comptes analytique")
    
class CaisseAttenteLineWizard(models.TransientModel):

    _inherit = 'caisse.attente.line.wizard'

    analitic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Compte analytique',
        )
    analytique_tag_ids = fields.Many2many('account.analytic.tag')

class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    caisse_id = fields.Many2one(
        'account.caisse',
        string='Caisse', check_company=True,
    )

    caisse_line_id = fields.Many2one(
        'account.caisse.line',
        string='Ligne de caisse externe',
    )