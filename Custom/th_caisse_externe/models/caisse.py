from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

from odoo import api, SUPERUSER_ID

def remove_company_id(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sequences = env['ir.sequence'].search([('code', '=', 'account.caisse')])
    for sequence in sequences:
        sequence.company_id = False

muz = (' ', 'Onze', 'Douze', 'Treize',
       'Quatorze', 'Quinze', 'Seize', 'Dix-Sept', 'Dix-Huit', 'Dix-Neuf')


to_19_fr = ('Zéro',  'Un',   'Deux',  'Trois', 'Quatre',   'Cinq',   'Six',
            'Sept', 'Huit', 'Neuf', 'Dix',   'Onze', 'Douze', 'Treize',
            'Quatorze', 'Quinze', 'Seize', 'Dix-Sept', 'Dix-Huit', 'Dix-Neuf')
tens_fr = ('Vingt', 'Trente', 'Quarante', 'Cinquante', 'Soixante',
           'Soixante-Dix', 'Quatre-Vingt', 'Quatre-Vingt Dix')
denom_fr = ('',
            'Mille',     'Million(s)',         'Milliards',       'Billions',       'Quadrillions',
            'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
            'Décillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
            'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Icosillion', 'Vigintillion')


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


class CategorieOperation(models.Model):

    _name = 'categorie.operation'
    _check_company_auto = True
    _description = 'Catégorie d\'opération'
    

    name = fields.Char(string="Nom", required=True)
    account_id = fields.Many2one(
        'account.account',
        string='Compte',
    )
    a_justifier = fields.Boolean(string="A justifier", required=True)
    is_partner = fields.Boolean(string="Est un compte partenaire")
    remboursement = fields.Boolean(string="Remboursement")
    type_operation = fields.Selection([
        ('0', 'Encaissement'),
        ('1','Décaissement')
    ], required=True)

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env.company
    )

    @api.onchange('a_justifier')
    @api.depends('a_justifier')
    def onchange_a_justifier(self):
        for rec in self:
            rec.is_partner = rec.is_partner


class AccountCaisseBilletageLine(models.Model):
    _name = 'account.caisse.billetage.line'
    _description = 'Linge de billetage'
    _check_company_auto = True

    nombre = fields.Float(string="Nombre de billet/pièce")
    valeur = fields.Float(string="Valeur")
    montant = fields.Float(string="Montant")
    balance = fields.Selection([('start', 'Solde initial'),('close','Solde final')], required=True)
    caisse_id = fields.Many2one(
        'account.caisse',
        string='Caisse',
        check_company=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env.company
    )

    @api.onchange('nombre','valeur')
    def onchange_nombre_valeur(self):
        for rec in self:
            rec.montant = rec.nombre * rec.valeur


class AccountCaisse(models.Model):
    _name = 'account.caisse'
    _inherit = ['mail.thread','mail.activity.mixin']
    _check_company_auto = True
    _description = 'Caisse'
    _rec_name="reference"

    move_line_ids = fields.One2many('account.move.line', 'caisse_id')
    operation_ids = fields.One2many('account.caisse.line', 'caisse_id', copy=True, track_visibility='always',
                                    string='Ajouter une opération', )

    reference = fields.Char(string="Référence", readonly=True, required=True, default="Nouveau")
    account_journal_id = fields.Many2one(
        'account.journal',
        track_visibility='always', string='Journal',
        required=True,
        related='type_id.journal_id'
    )

    type_id = fields.Many2one(
        'type.caisse',
        track_visibility='always', string='Type de caisse',
        )
    date_start = fields.Datetime(sting="Date début", required=True) 
    date_end = fields.Datetime(sting="Date de fin", required=True) 
    solde_initial = fields.Float(track_visibility='always', string="Solde initial", compute="get_solde_initial", store=True)
    solde_final = fields.Float(track_visibility='always', string="Solde final")
    solde_calcule = fields.Float(track_visibility='always', string="Solde calculé", store=True, compute="get_total_entree_sortie")
    currency_id = fields.Many2one(
        'res.currency', store=True, compute="get_currency",
        track_visibility='always', string='Devise'
    )
    user_id = fields.Many2one(
        'res.users',
        track_visibility='always', string='Responsable', default=lambda self: self.env.user.id, readonly=True
        )

    # user_id = fields.Many2one(
    #     'res.users',
    #     string='Caissier',
    #     default=lambda self: self.env.user.id,
    #     readonly=True,
    # )

    note = fields.Char(track_visibility='always', string="Commentaire")



    move_ids = fields.One2many('account.move', 'caisse_id')

    billetage_ids = fields.One2many('account.caisse.billetage.line', 'caisse_id')

    account_move_total = fields.Integer(
        string='Total',
        compute="_get_accout_move_count"
    )


    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env.company
    )
    
    total_entree = fields.Float(
        string="Total entrée",
        compute='get_total_entree_sortie'
    )

    total_sortie = fields.Float(
        string="Total sortie",
        compute='get_total_entree_sortie'
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('posted', 'Posté'),
        ('canceled', 'Annuler'),
          ],
        default='draft'
    )

    state_change = fields.Boolean(
        string="Etat changé",
        default=False
    )


    @api.onchange('state')
    def onchange_state(self):
        """
        La fonction retuourne False si le statut est draft sinon True
        """
        for rec in self:
            rec.state_change = rec.state != 'draft'



    def _get_accout_move_count(self):
        for rec in self:
            move_ids = self.env['account.move'].search([('caisse_id', '=', rec.id)])
            rec.account_move_total = len(move_ids)
            rec.move_line_ids = rec.move_ids.line_ids.ids

    def account_move_list(self):
        return {
            'name': ('Pièces comptables'),
            'domain': [('caisse_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.onchange('type_id', 'account_journal_id', 'date_start', 'date_end')
    @api.depends('type_id', 'account_journal_id', 'date_start', 'date_end')
    def get_currency(self):
        for rec in self:
            rec.currency_id = rec.type_id.currency_id.id

    def billetage_id(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Billetage',
            'view_mode': 'form',
            'res_model': 'caisse.billetage',
            'res_id': False,
            'context': {'default_caisse_id': self.id},
            'target': 'new',
        }

    
    @api.depends('account_journal_id','type_id')
    def get_solde_initial(self):
        for rec in self:
            rec.solde_initial = rec.type_id.solde_caisse

    @api.onchange('operation_ids')
    @api.depends('account_journal_id','type_id')
    def get_total_entree_sortie(self):
        for rec in self:
            solde = 0
            total_entree = 0
            total_sortie = 0
            for line in rec.operation_ids:
                solde += line.currency_amount
                if line.montant >= 0:
                    total_entree +=  line.currency_amount
                else:
                    total_sortie +=  abs(line.currency_amount)
            rec.total_entree = total_entree
            rec.total_sortie = total_sortie
            rec.solde_calcule = rec.solde_initial + solde

    def ecritures_comptables(self):
        return{
            'name':('Ecritures comptables'),
            'domain':[('caisse_id','=', self.id)],
            'res_model':'account.move.line',
            'view_id':False,
            'view_mode':'tree,form',
            'type':'ir.actions.act_window',
        }
        
    @api.model
    def create(self, values):
        type_caisse  =  self.env['type.caisse'].browse(int(values['type_id']))
        sequence = self.env['ir.sequence'].next_by_code('account.caisse')
        date_start = datetime.strptime( values['date_start'], '%Y-%m-%d %H:%M:%S')
        dante_end = datetime.strptime( values['date_end'], '%Y-%m-%d %H:%M:%S')
        ref = '{} N° {} DU {} AU {}'.format(type_caisse.name,sequence, date_start.strftime('%d/%m/%y %H:%M:%S'), dante_end.strftime('%d/%m/%y %H:%M:%S'))
        values['reference'] = ref
        result = super().create(values)
        caisses = self.env['account.caisse'].search([
            ('date_start','>=', values['date_start']),
            ('date_end','<=', values['date_end']),
            ('type_id','=', values['type_id'])
        ])
        # if len(caisses)>1:
        #     raise UserError(_('Vous ne pouvez pas créer une caisse à cette date. Une autre caisse existe déjà sur cette date'))
        return result
    
    def unlink(self):
        for rec in self:
            if rec.state in ['confirmed','posted']:
                raise UserError(_('Impossible de supprimer le relevé dans cet état'))
        res = super().unlink()
        return res

    def poster_comptabilite_caisse_p(self):
        for rec in self:
            if rec.type_id.auto_post:
                for move_id in rec.move_ids:
                    move_id.action_post()
            for line in rec.operation_ids:
                if line.move_id:
                    line.post_account_move_payment()
            rec.state = 'posted'

    def confirmer_caisse(self):
        for rec in self:
            if len(rec.operation_ids) <= 0:
                raise UserError(_('Pas encore d\'opérations'))
            if rec.solde_final != rec.solde_calcule:
                raise UserError(_('Le solde final est diférrent du solde calculé ! {} - {}'.format(rec.solde_final,rec.solde_calcule)))
            for line in rec.operation_ids:
                line.caise_type_id = rec.type_id.id
                if line.state == 'draft':
                    line.state = 'confirmed'
            if rec.state == 'draft':
                rec.state = 'confirmed'
                rec.type_id.solde_caisse = rec.solde_final

    def annuler_caisse(self):
        for rec in self:
            rec.type_id.solde_caisse = rec.solde_initial
            for line in rec.operation_ids:
                line.state = 'canceled'
            rec.state = 'canceled'

    def mettre_brouillon(self):
        for rec in self:
            rec.type_id.solde_caisse = rec.solde_initial
            for line in rec.operation_ids:
                line.state = 'draft'
            rec.state = 'draft'

    # open_cashbox_id = fields.Many2one(
    #     'account.bank.statement.cashbox',
    #     string='Open CAshbox Id',
    # )



