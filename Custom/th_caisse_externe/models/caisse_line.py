from odoo import _, api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


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


class AccountCaisseLine(models.Model):
    _name = 'account.caisse.line'
    _check_company_auto = True
    _description = 'Opérations de caisse'
    _rec_name = 'reference'

    reference = fields.Char(
        string="Référence",
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Facture',
    )

    account_invoice_ids = fields.Many2many(
        comodel_name='account.move',
        string='LES FACTURES',
        check_company=True,
        compute='_get_invoice_by_partners',
        store=True,
        readonly=False
    )

    date = fields.Datetime(
        string="Date",
        required=True,
        default=fields.Datetime.now
    )

    libelle = fields.Char(
        string="Libellé",
        required=True
    )

    piece_joint = fields.Binary(
        string="Pièce jointe"
    )

    note = fields.Char(
        string="Commentaire"
    )

    a_justifier = fields.Boolean(
        string="A justifier",
        default=False
    )

    montant_justifier = fields.Float(
        string="Montant justifier"
    )

    entree = fields.Float(
        string="Entrée",
        compute="get_solde"
    )

    sortie = fields.Float(
        string="Sortie",
        compute="get_solde"
    )

    solde = fields.Float(
        string="solde",
        store=True,
        compute="get_solde"
    )

    ecart_sur_montant = fields.Float(
        string='Ecart de justification'
    )

    taux = fields.Float(
        string='Taux de change'
    )

    reference_origine = fields.Many2one(
        'account.caisse.line',
        string='Référence d\'origine',
        check_company=True,
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

    # les champs du module th_caisse_externe_analytique

    analitic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Compte analytique',
        store=True
    )

    analytic_precision = fields.Integer(
        string="Précision analytique",
        default=2,
        help="Nombre de décimales utilisées pour la répartition analytique."
    )

    analytic_distribution = fields.Json(
        string='Répartition analytique',
        help="Permet de répartir le montant sur plusieurs comptes analytiques.",
        default=dict
    )

    compte_analytique = fields.Boolean(
        string="Accepter les comptes analytique",
        related='categorie_id.compte_analytique'
    )

    montant = fields.Float(
        string="Montant"
    )

    categorie_id = fields.Many2one(
        'categorie.operation',
        string='Categorie d\'opération', check_company=True,
    )

    model_id = fields.Many2one(
        'account.reconcile.model',
        string='Model de reconciliation',
        check_company=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True,
        ondelete='restrict',
        default=lambda self: self.env.company

    )

    caisse_id = fields.Many2one(
        'account.caisse',
        string='Caisse', check_company=True,
    )

    beneficiaire = fields.Char(string='Bénéficiaire')

    montant_en_lettre = fields.Char(
        string="Montant en lettre",
        compute="calcul_montant_en_lettre"
    )

    caise_type_id = fields.Many2one(
        'type.caisse',
        string='Type de caisse', check_company=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Caissier',
        default=lambda self: self.env.user.id,
        readonly=True,
    )

    currency_amount = fields.Float(
        string="Montant en devise de référence",
        compute="get_currency_amount"
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('posted', 'Comptabilisé'),
        ('canceled', 'Annulé'),
    ], default='draft')

    account_id = fields.Many2one(
        'account.account', check_company=True,
        string='Compte',
    )

    currency_id = fields.Many2one(
        'res.currency', store=True,
        track_visibility='always',
        string='Devise',
    )

    full_name = fields.Char(compute="get_full_name")

    def get_full_name(self):
        for rec in self:
            name = rec.libelle
            if rec.move_id:
                name = "{} - {}".format(rec.libelle, rec.move_id.name)
            rec.full_name = name

    @api.depends('partner_id')
    def _get_invoice_by_partners(self):
        for rec in self:
            move_ids = self.env['account.move'].search(
                [
                    ('move_type', 'in', ['out_invoice', 'in_invoice']),
                    ('payment_state', '!=', 'paid'),
                    ('state', '=', 'posted'),
                    ('partner_id', 'in', rec.partner_id.ids),
                ]
            )
            if move_ids:
                rec.account_invoice_ids = move_ids.ids


    def get_analytic_display(self):
        if self.analytic_distribution:
            lines = []
            for acc_id, percent in self.analytic_distribution.items():
                acc = self.env['account.analytic.account'].browse(int(acc_id))
                lines.append(f"{acc.name} : {round(percent, 2)} %")
            return lines
        elif self.analitic_account_id:
            return [self.analitic_account_id.name]
        return []

    def poster_operation(self):
        for rec in self:
            if not rec.move_id:
                company_currency = rec.company_id.currency_id
                current_currency = rec.currency_id
                is_foreign_currency = (company_currency != current_currency)
                montant = abs(rec.montant)

                amount_value = current_currency._convert(
                    montant,
                    company_currency,
                    rec.company_id,
                    rec.date or fields.Date.today()
                )

                currency_id = current_currency.id
                amount_currency = montant if is_foreign_currency else abs(rec.currency_amount)
                lines = []

                if rec.state == 'draft':
                    account_id = rec.account_id.id
                    caisse_account_id = rec.caisse_id.account_journal_id.default_account_id.id
                    type_operation = rec.categorie_id.type_operation

                    if type_operation == '1':  # ENCAISSEMENT
                        vals_debit_dict = {
                            'account_id': account_id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.libelle,
                            'amount_currency': amount_currency,
                            'currency_id': currency_id,
                            'debit': amount_value,
                            'credit': 0,
                            'caisse_id': rec.caisse_id.id,
                            'caisse_line_id': rec.id,
                            'categorie_id': rec.categorie_id.id,
                        }

                        vals_credit_dict = {
                            'account_id': caisse_account_id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.libelle,
                            'amount_currency': -amount_currency,
                            'currency_id': currency_id,
                            'debit': 0,
                            'credit': amount_value,
                            'caisse_id': rec.caisse_id.id,
                            'caisse_line_id': rec.id,
                            'categorie_id': rec.categorie_id.id,
                        }

                    else:  # DECAISSEMENT
                        vals_debit_dict = {
                            'account_id': caisse_account_id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.libelle,
                            'amount_currency': amount_currency,
                            'currency_id': currency_id,
                            'debit': amount_value,
                            'credit': 0,
                            'caisse_id': rec.caisse_id.id,
                            'caisse_line_id': rec.id,
                            'categorie_id': rec.categorie_id.id,
                        }

                        vals_credit_dict = {
                            'account_id': account_id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.libelle,
                            'amount_currency': -amount_currency,
                            'currency_id': currency_id,
                            'debit': 0,
                            'credit': amount_value,
                            'caisse_id': rec.caisse_id.id,
                            'caisse_line_id': rec.id,
                            'categorie_id': rec.categorie_id.id,
                        }

                    if rec.compte_analytique:
                        vals_debit_dict['analytic_distribution'] = rec.analytic_distribution
                        vals_credit_dict['caisse_id'] = rec.caisse_id.id
                        vals_credit_dict['caisse_line_id'] = rec.id

                    vals_debit = (0, 0, vals_debit_dict)
                    vals_credit = (0, 0, vals_credit_dict)

                    lines.append(vals_debit)
                    lines.append(vals_credit)

                    code = rec.caisse_id.account_journal_id.code or 'CSH'
                    year = rec.date.strftime('%Y%m%d%H%M%S')
                    seq_number = self.env['ir.sequence'].next_by_code('account.move')
                    ref = f'{code}/{rec.caisse_id.type_id.name}-{year}/{seq_number}'

                    move_vals = {
                        'journal_id': rec.caisse_id.account_journal_id.id,
                        'date': rec.date,
                        'name': ref,
                        'caisse_id': rec.caisse_id.id,
                        'caisse_line_id': rec.id,
                        'categorie_id': rec.categorie_id.id,
                        'company_id': rec.company_id.id,
                        'line_ids': lines,
                    }

                    move = self.env['account.move'].create(move_vals)

                    rec.caisse_id.type_id.solde_caisse = rec.caisse_id.solde_calcule

                    return move

    def write(self, values):
        res = super().write(values)
        # 1. Vérification de la date par rapport à la période de la caisse
        if values.__contains__('date'):
            line_date = datetime.strptime(values['date'], '%Y-%m-%d %H:%M:%S')
            date_start = self.caisse_id.date_start
            date_end = self.caisse_id.date_end
            if line_date < date_start or line_date > date_end:
                raise UserError(_('Veuillez vérifier la date svp !'))

        # 2. Recherche des pièces comptables liés
        move_ids = self.env['account.move'].search([('caisse_line_id', '=', self.id)])

        if not self.move_id:
            # Cas où aucune écriture comptable directe n’est liée
            if self.state == "draft":
                if move_ids:
                    for move in move_ids:
                        if move.state == 'posted':
                            move.button_draft()
                        if move.state in ['draft', 'cancel']:
                            move.unlink()
                self.poster_operation()
        else:
            # Une pièce comptable existe
            if move_ids:
                for move in move_ids:
                    if move.state == 'posted':
                        move.button_draft()
                    if move.state in ['draft', 'cancel']:
                        move.unlink()

            # On reposte uniquement si confirmé
            if self.state == "confirmed":
                self.poster_operation()

        return res

    @api.model
    def create(self, vals):
        line_date = datetime.strptime(str(vals['date']), '%Y-%m-%d %H:%M:%S')
        caisse_id = self.env['account.caisse'].search([('id', '=', vals['caisse_id'])], limit=1)
        date_start = caisse_id.date_start
        date_end = caisse_id.date_end
        caisse_name = self.env['account.caisse'].browse(int(vals['caisse_id'])).type_id.name.replace(' ', '_')
        if line_date < date_start or line_date > date_end:
            raise UserError(_('Veuillez vérifier la date svp !'))

        vals['reference'] = self.env['ir.sequence'].next_by_code(
            caisse_name) or 'Nouveau'

        result = super(AccountCaisseLine, self).create(vals)
        if not vals['move_id']:
            result.poster_operation()
        return result


    def action_print_th_caisse_externe_line_report(self):
        try:
            return self.env.ref('th_caisse_externe.th_caisse_externe_line_report').report_action(self)
        except Exception as e:
            raise UserError(_('Le rapport n\'est pas disponible: %s' % e))


    @api.onchange('move_id')
    def onchange_move_id(self):
        for rec in self:
            if rec.categorie_id.type_operation == '1':
                rec.montant = rec.move_id.amount_residual * -1
            else:
                rec.montant = abs(rec.move_id.amount_residual)
            if rec.move_id:
                rec.currency_id = rec.move_id.currency_id.id,
                if rec.move_id.move_type == 'in_invoice':
                    rec.account_id = rec.move_id.partner_id.property_account_payable_id.id
                elif rec.move_id.move_type == 'out_invoice':
                    rec.account_id = rec.move_id.partner_id.property_account_receivable_id.id

    @api.onchange('categorie_id', 'partner_id')
    def onchange_partner_id(self):
        for rec in self:
            type_invoice = 'out_invoice'
            if rec.categorie_id.type_operation == '1':
                type_invoice = 'in_invoice'
            return {'domain': {'move_id': [
                ('partner_id', '=', rec.partner_id.id),
                ('state', '=', 'posted'),
                ('invoice_payment_state', 'not in', ['paid']),
                ('move_type', '=', type_invoice),
            ]}}

    @api.onchange('caisse_id', 'date')
    @api.depends('caisse_id', 'date')
    def _get_currency_id(self):
        self.currency_id = self.caisse_id.currency_id.id

    @api.depends('montant', 'currency_id')
    def get_currency_amount(self):
        for rec in self:
            if rec.currency_id and rec.caisse_id and rec.caisse_id.currency_id:
                rec.currency_amount = rec.currency_id._convert(
                    rec.montant,
                    rec.caisse_id.currency_id,
                    self.env.company,
                    fields.Date.today()
                )
            else:
                rec.currency_amount = rec.montant

    @api.onchange('montant')
    @api.depends('montant')
    def get_solde(self):
        for rec in self:
            sortie = 0
            entree = 0
            if rec.montant < 0:
                sortie = rec.montant
            else:
                entree = rec.montant
            rec.sortie = abs(sortie)
            rec.entree = abs(entree)
            rec.solde = rec.caisse_id.solde_initial - abs(rec.sortie) + rec.entree

    @api.onchange('categorie_id')
    def onchange_categorie_id(self):
        for rec in self:
            account_id = None
            if rec.type_partenaire == 'client':
                account_id = rec.partner_id.property_account_receivable_id.id
            elif rec.type_partenaire == 'salarie':
                account_id = rec.partner_id.compte_salarie_id.id
            elif rec.type_partenaire == 'fournisseur':
                account_id = rec.partner_id.property_account_payable_id.id
            else:
                account_id = rec.categorie_id.account_id.id
            rec.account_id = account_id

    def convertir_montant(self, montant, devise_cible):
        # Récupérer le taux de change entre la devise d'origine et la devise cible
        taux_change = self.env['res.currency']._get_conversion_rate(self.currency_id, devise_cible)

        # Convertir le montant dans la devise cible
        montant_converti = montant * taux_change

        return montant_converti

    def post_account_move_payment(self):
        for rec in self:
            payment_vals = None
            if rec.move_id.move_type == 'in_invoice':
                payment_vals = {
                    'payment_type': 'outbound',
                    'partner_id': rec.partner_id.id,
                    'amount': abs(rec.montant),
                    'date': rec.date,
                    'caisse_id': rec.caisse_id.id,
                    'caisse_line_id': rec.id,
                    'ref': rec.full_name,
                    'partner_type': 'supplier',
                    'payment_method_id': 1,
                    'currency_id': rec.currency_id.id,
                    'company_id': rec.company_id.id,
                    'journal_id': rec.caisse_id.account_journal_id.id,
                    # 'invoice_ids': [(4, rec.move_id.id)],
                }
            else:
                payment_vals = {
                    'payment_type': 'inbound',
                    'partner_id': rec.partner_id.id,
                    'amount': rec.montant,
                    'date': rec.date,
                    'caisse_line_id': rec.id,
                    'caisse_id': rec.caisse_id.id,
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'currency_id': rec.currency_id.id,
                    'ref': rec.full_name,
                    'journal_id': rec.caisse_id.account_journal_id.id,
                    # 'invoice_ids': [(4, rec.move_id.id)],
                }
            # raise UserError(_(payment_vals))
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            rec.move_id.message_post(body=f'Payment of {payment.amount} created and posted.')

    @api.onchange('date')
    def onchange_date(self):
        for rec in self:
            if rec.date:
                if rec.date < rec.caisse_id.date_start or rec.date > rec.caisse_id.date_end:
                    raise UserError(_('Veuillez vérifier la date svp !'))

    @api.onchange('montant', 'categorie_id')
    def onchange_montant_categorie_id(self):
        for rec in self:
            if rec.categorie_id.is_partner:
                if not rec.partner_id:
                    raise UserError(_('Vous devez obligatoire sélectionner un partenaire'))
            if rec.categorie_id.type_operation == '1' or rec.categorie_id.remboursement:
                if rec.montant >= 0:
                    rec.montant = rec.montant * -1
            else:
                rec.montant = abs(rec.montant)

    @api.onchange('montant', 'currency_amount')
    def onchange_montant(self):
        for rec in self:
            caisse = rec.caisse_id
            if caisse.type_id.seuil_maximal:
                if (caisse.solde_calcule + rec.currency_amount) >= caisse.type_id.seuil_maximal:
                    raise UserError(
                        _(f'Vous avez atteint le seuil maximal de {caisse.type_id.seuil_maximal} ! Veuillez faire un décaissement'))
            if rec.currency_amount != 0:
                if (-rec.currency_amount) > caisse.solde_calcule:
                    rec.currency_amount = 0
                    raise UserError(
                        _(f'Le solde de votre compte ne vous permet pas d\'effectuer cette opération. Solde caisse {caisse.solde_calcule}'))


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
                    if (val > 70 and val <= 79):
                        dcap = 'Soixante'
                        return dcap + '-' + muz[val % 10]

                    if (val > 90 and val <= 99):
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
        final_result = start_word + ' ' + units_name + \
                       ' ' + end_word + ' ' + cents_name + ' '
        return final_result.lower()
