# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
class OperationJustifier(models.TransientModel):

    _name = 'operation.justifier'
    _description = 'Justifier une opération'
    _check_company_auto = True

    operation_id = fields.Many2one(
        'account.caisse.line',
        string='operation',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire',
    )
    type_partenaire = fields.Selection([
        ('client', 'Client'),
        ('fournisseur', 'Fournisseur'),
        ('salarie', 'Salarié'),
        ('autre', 'Autre'),
    ])
    date_operation = fields.Date(string="Date", default=datetime.now())
    currency_amount = fields.Float(string="Montant à justifier")
    diffenrence = fields.Float(string="Différence de change")
    montant = fields.Float(string="Montant initial")
    a_justifier = fields.Float(string='Reste à justifier')
    total_justifie = fields.Float(string='Total justifié')
    caisse_id = fields.Many2one(
        'account.caisse',
        string='Caisse',
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
    )
    
    line_ids = fields.One2many('caisse.attente.line.wizard', 'operation_id')

    @api.onchange('operation_id','caisse_id')
    @api.depends('operation_id','montant','type_partenaire','date_operation','caisse_id')
    def _get_all_date(self):
        for rec in self:
            rec.date_operation = rec.operation_id.date
            rec.montant = rec.operation_id.montant
            rec.caisse_id = rec.operation_id.caisse_id.id
            rec.a_justifier = rec.operation_id.montant - rec.total_justifie
            rate_usd = self.env['res.currency'].search([('name', '=', rec.caisse_id.account_journal_id.currency_id.name)], limit=1)
            rec.type_partenaire = rec.operation_id.type_partenaire
            rec.partner_id = rec.operation_id.partner_id.id
            rec.currency_amount = rec.operation_id.currency_amount
            rec.currency_id = rec.operation_id.currency_id.id
            

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        for rec in self:
            total = 0
            base_currency = self.env.ref('base.main_company').currency_id
            caisse_currency = self.operation_id.caisse_id.currency_id
            for line in rec.line_ids:
                if line.currency_id.id == base_currency.id:
                    total += line.montant
                else:
                    total += (line.montant / line.currency_id.rate)
            rec.total_justifie = total
            rec.a_justifier = (rec.operation_id.montant / caisse_currency.rate ) - rec.total_justifie
            rec.diffenrence = rec.currency_amount - total

    def valide_operation(self):
        base_currency = self.operation_id.caisse_id.currency_id #self.env.ref('base.main_company').currency_id
        caisse_account_id = self.operation_id.caisse_id.account_journal_id.default_debit_account_id.id
        journal_id = self.operation_id.caisse_id.account_journal_id.id
        compte_perte_id = int(self.env['ir.config_parameter'].sudo().get_param('th_caisse_externe.compte_perte_id'))
        compte_gain_id = int(self.env['ir.config_parameter'].sudo().get_param('th_caisse_externe.compte_gain_id'))

        for line in self.line_ids:
            line.poster_operation(self.partner_id, caisse_account_id, journal_id, self.operation_id)

        lines = []
        account_id = self.partner_id.compte_salarie_id.id
        journal_id =  int(self.env['ir.config_parameter'].sudo().get_param('th_caisse_externe.journal_id'))
        if self.diffenrence > 0:            
            vals_credit=(0,0,{
                'account_id': compte_gain_id,
                'partner_id': self.partner_id.id,
                'caisse_id': self.caisse_id.id,
                'name':'Gain de change',
                'amount_currency':-(-self.diffenrence) / self.currency_id.rate,
                'currency_id': self.caisse_id.account_journal_id.currency_id.id if (self.currency_id.id == base_currency.id) else None,
                'debit':0,
                'credit':abs(self.diffenrence)/base_currency.rate,
            })
            vals_debit=(0,0,{
                'account_id': account_id,
                'partner_id': self.operation_id.partner_id.id,
                'caisse_id': self.caisse_id.id,
                'name':'Gain de change',
                'amount_currency':(-self.diffenrence)/ self.currency_id.rate,
                'currency_id': self.caisse_id.account_journal_id.currency_id.id if (self.currency_id.id == base_currency.id) else None,
                'debit':abs(self.diffenrence)/base_currency.rate,
                'credit':0,
            })
            lines.append(vals_credit)
            lines.append(vals_debit) 
        if self.diffenrence < 0:
            vals_credit=(0,0,{
                'account_id': account_id,
                'partner_id': self.partner_id.id,
                'caisse_id': self.caisse_id.id,
                'name':"Perte de change",
                'amount_currency':-(-self.diffenrence) / self.caisse_id.currency_id.rate,
                'currency_id': self.caisse_id.account_journal_id.currency_id.id if (self.caisse_id.currency_id.id == base_currency.id) else None,
                'debit':0,
                'credit':abs(self.diffenrence),
            })
            vals_debit=(0,0,{
                'account_id': compte_perte_id,
                'partner_id': self.operation_id.partner_id.id,
                'caisse_id': self.caisse_id.id,
                'name':"Perte de change",
                'amount_currency':(-self.diffenrence)/ self.caisse_id.currency_id.rate,
                'currency_id': self.caisse_id.account_journal_id.currency_id.id if (self.caisse_id.currency_id.id == base_currency.id) else None,
                'debit':abs(self.diffenrence),
                'credit':0,
            })
            lines.append(vals_credit)
            lines.append(vals_debit)    
        account_move_vals={
            'journal_id': journal_id,
            'ref': self.operation_id.reference,
            'date': self.date_operation,
            'company_id':self.env['res.company']._company_default_get('th_caisse_externe').id,
            'line_ids':lines,
        }

        if lines:
            result = self.env['account.move'].create(account_move_vals)
            if self.caisse_id.type_id.auto_post:
                result.action_post()
            self.operation_id.a_justifier = False


class CaisseAttenteLineWizard(models.TransientModel):

    _name = 'caisse.attente.line.wizard'
    _description = 'Ligne'

    date = fields.Date(string="Date", required=True, default=datetime.now())
    libelle = fields.Char(string="Libellé", required=True)
    note = fields.Char(string="Commentaire")
    a_justifier = fields.Boolean(string="A justifier", default=False)
    montant_justifier = fields.Float(string="Montant justifier")
    montant_devise = fields.Float(string='Montant en devise ref')
    ecart_sur_montant = fields.Float(string='Ecart de justification')
    taux = fields.Float(string='Taux de change')
    taux_de_change = fields.Float(string='Taux de change de l\'opération')
    caisse_line_id = fields.Many2one(
        'account.caisse.line',
        string='operation',
    )
    montant = fields.Float(string="Montant opération")
    categorie_id = fields.Many2one(
        'categorie.operation',
        string='Categorie d\'opération', 
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get('th_caisse_externe').id
        
        )
    caisse_id = fields.Many2one(
        'account.caisse',
        string='Caisse',         
    )

    user_id = fields.Many2one(
	    'res.users',
	    string='Caissier',
	    default=lambda self: self.env.user.id,
	    readonly=True,
	)
    operation_id = fields.Many2one(
        'operation.justifier',
        string='Opération',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
    )
    est_remboursement = fields.Boolean(string="Est un rembourssent")

    # les champs du module th_caisse_externe_analytique

    analitic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Compte analytique',
    )

    # analytique_tag_ids = fields.Many2many('account.analytic.tag')

    @api.onchange('montant_devise','montant')
    def onchange_montant_montant_devise(self):
        for rec in self:
            if rec.montant_devise and rec.montant:
                rec.taux_de_change = abs(rec.montant / rec.montant_devise)

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for rec in self:
            rec.taux = abs(rec.currency_id.rate)
    

    @api.onchange('montant','categorie_id')
    def onchange_montant_categorie_id(self):
        for rec in self:
            if rec.categorie_id.type_operation == '1'or rec.categorie_id.remboursement:
                if rec.montant >= 0:
                    rec.montant = rec.montant * -1
            else:
                rec.montant = abs(rec.montant)

    @api.onchange('currency_id')
    def calcul_devise_rate(self):
        rate_usd = self.env.ref('base.main_company').currency_id
        if self.currency_id == rate_usd.id:
            self.taux = 1
        else:
            self.taux = rate_usd.rate

        
    def poster_operation(self, partner_id,caisse_account_id, journal_id, operation_id):
        account_id = partner_id.compte_salarie_id.id 
        base_currency = self.env.ref('base.main_company').currency_id
        lines = []

        if self.est_remboursement:
            vals={
                'date': self.date,
                'libelle': self.libelle,
                'note':self.note,
                'reference_origine': self.operation_id.operation_id.id,
                'type_partenaire':self.operation_id.operation_id.type_partenaire,
                'partner_id':partner_id.id,
                'montant': - self.montant,
                'categorie_id': self.categorie_id.id,
                'caisse_id':self.caisse_id.id,
            }
            self.env['account.caisse.line'].create(vals)
        else:                
            vals_credit=(0,0,{
                'account_id': self.categorie_id.account_id.id,
                'partner_id': partner_id.id,
                'name':self.libelle,
                'caisse_id': self.operation_id.operation_id.caisse_id.id,
                'amount_currency':abs(self.montant)if (self.currency_id.id != base_currency.id) else None,
                'currency_id': self.operation_id.caisse_id.account_journal_id.currency_id.id if (self.currency_id.id != base_currency.id) else None,
                'debit':(abs(self.montant)/self.taux),
                'credit':0,
            })
            vals_debit=(0,0,{
                'account_id': account_id,
                'partner_id': self.operation_id.partner_id.id,
                'name':self.libelle,
                'caisse_id': self.operation_id.operation_id.caisse_id.id,
                'amount_currency':-abs(self.montant)if (self.currency_id.id != base_currency.id) else None,
                'currency_id': self.operation_id.caisse_id.account_journal_id.currency_id.id if (self.currency_id.id != base_currency.id) else None,
                'debit':0,
                'credit':(abs(self.montant)/self.taux),
            })
            lines.append(vals_credit)
            lines.append(vals_debit)            
            accout_move_vals={
                'journal_id': journal_id,
                'date':self.date,
                'company_id':self.company_id.id,
                'line_ids':lines,
            }
            
            result = self.env['account.move'].create(accout_move_vals)
           
            if self.operation_id.caisse_id.type_id.auto_post:
                    result.action_post()