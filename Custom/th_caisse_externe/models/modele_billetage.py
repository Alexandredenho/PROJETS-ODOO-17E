from odoo import fields, models, api, _


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

    @api.onchange('nombre', 'valeur')
    def onchange_nombre_valeur(self):
        for rec in self:
            rec.montant = rec.nombre * rec.valeur


class AccountCaisseBilletageLine(models.Model):
    _name = 'account.caisse.billetage.line'
    _description = 'Linge de billetage'
    _check_company_auto = True

    nombre = fields.Float(string="Nombre de billet/pièce")
    valeur = fields.Float(string="Valeur")
    montant = fields.Float(string="Montant")

    balance = fields.Selection(
        selection=[
            ('start', 'Solde initial'),
            ('close','Solde final')
        ], required=True
    )

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