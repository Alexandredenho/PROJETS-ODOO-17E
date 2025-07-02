from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError




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

class SortieAttente(models.Model):
    _name = 'sortie.attente'
    _description = 'Sortie en attente'
    _rec_name = 'reference'

    reference = fields.Char(string="Référence", copy=False, readonly=True, default="Nouveau")
    def _get_date(self):
        return self.caisse_id.date_start
    date = fields.Date(string="Date", required=True, default=_get_date)
    libelle = fields.Char(string="Libellé", required=True)
    note = fields.Char(string="Commentaire")
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
    montant = fields.Float(string="Montant")
    categorie_id = fields.Many2one(
        'categorie.operation',
        string='Categorie d\'opération',
        )
    model_id = fields.Many2one(
        'account.reconcile.model',
        string='Model de reconciliation',
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
    beneficiaire = fields.Char(string='Bénéficiaire')
    montant_en_lettre = fields.Char(
        string="Montant en lettre", compute="calcul_montant_en_lettre")

    caise_type_id = fields.Many2one(
        'type.caisse',
        string='Type de caisse',
    )
    user_id = fields.Many2one(
	    'res.users',
	    string='Caissier',
	    default=lambda self: self.env.user.id,
	    readonly=True,
	)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed','Confirmé'),
        ('cancel','Annuler'),
        ('posted','Comptabilisé')
    ], default='draft')

    def confirmer_caisse(self):
        for rec in self:
            rec.state = 'confirmed'

    def annuler_caisse(self):
        for rec in self:
            rec.state = 'cancel'

    def mettre_brouillon(self):
        for rec in self:
            rec.state = 'draft'

    def poster_comptabilite_caisse(self):
        for rec in self:
            rec.state = 'posted'

    def calcul_montant_en_lettre(self):
        for rec in self:
            rec.montant_en_lettre = self.amount_to_text_fr(self.montant)

    def _convert_nn_fr(self, val):
        """ convertion des valeurs < 100 en Français """
        if val < 20:
            return to_19_fr[val]
        for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_fr)):
            if dval + 10 > val:
                if val % 10:
                    if(val > 70 and val <= 79):
                        dcap = 'Soixante'
                        return dcap + '-' + muz[val % 10]

                    if(val > 90 and val <= 99):
                        dcap = 'Quatre-vingt'
                        return dcap + '-' + muz[val % 10]
                    else:
                        return dcap + '-' + to_19_fr[val % 10]

                return dcap

    def _convert_nnn_fr(self, val):
        """ convert a value < 1000 to french

            special cased because it is the level that kicks 
            off the < 100 special case.  The rest are more general.  This also allows you to
            get strings in the form of 'forty-five hundred' if called directly.
        """
        word = ''
        (mod, rem) = (val % 100, val // 100)
        b = val // 100
        if rem > 0:
            if b == 1:
                word = 'Cent'
            else:
                word = to_19_fr[rem] + ' Cent'
        if mod > 0:
            word += ' '
        if mod > 0:
            word += self._convert_nn_fr(mod)
        return word

    def french_number(self, val):
        if val < 100:
            return self._convert_nn_fr(val)
        if val < 1000:
            return self._convert_nnn_fr(val)
        for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_fr))):
            if dval > val:
                mod = 1000 ** didx
                l = val // mod
                r = val - (l * mod)
                if (l == 1) and (denom_fr[didx] == 'Mille'):
                    ret = denom_fr[didx]
                else:
                    ret = self._convert_nnn_fr(l) + ' ' + denom_fr[didx]
                if r > 0:
                    ret = ret + ' ' + self.french_number(r)
                return ret

    def amount_to_text_fr(self, number):
        number = '%.2f' % number
        units_name = ' '
        list = str(number).split('.')
        muzamil = (self.french_number(abs(int(list[0]))))
        start_word = muzamil
        end_word = ''
        # french_number(int(list[1]))
        cents_number = int(list[1])
        cents_name = (cents_number > 1) and ' ' or ' '
        final_result = start_word + ' '+units_name + \
            ' ' + end_word + ' ' + cents_name + ' '
        return final_result.lower()