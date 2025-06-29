from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval

class CaisseSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    compte_perte_id = fields.Many2one(
        'account.account',
        string='Compte de perte de change',
        domain="[('company_id', '=', company_id)]"
    )
    compte_gain_id = fields.Many2one(
        'account.account',
        string='Compte de gain de change',
        domain="[('company_id', '=', company_id)]"
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal de difference de change',
        domain="[('company_id', '=', company_id)]"
    )

    @api.model
    def set_values(self):
        res = super(CaisseSettings, self).set_values()
        company_id = self.env.company.id

        self.env['ir.config_parameter'].set_param('th_caisse_externe.compte_perte_id_{}'.format(company_id), self.compte_perte_id.id)
        self.env['ir.config_parameter'].set_param('th_caisse_externe.compte_gain_id_{}'.format(company_id), self.compte_gain_id.id)
        self.env['ir.config_parameter'].set_param('th_caisse_externe.journal_id_{}'.format(company_id), self.journal_id.id)
        
        return res

    @api.model
    def get_values(self):
        res = super(CaisseSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        company_id = self.env.company.id

        _compte_perte_id = int(ICPSudo.get_param('th_caisse_externe.compte_perte_id_{}'.format(company_id), default=0))
        _compte_gain_id = int(ICPSudo.get_param('th_caisse_externe.compte_gain_id_{}'.format(company_id), default=0))
        _journal_id = int(ICPSudo.get_param('th_caisse_externe.journal_id_{}'.format(company_id), default=0))

        res.update(
            compte_perte_id=_compte_perte_id if _compte_perte_id else False,
            compte_gain_id=_compte_gain_id if _compte_gain_id else False,
            journal_id=_journal_id if _journal_id else False
        )
        return res
