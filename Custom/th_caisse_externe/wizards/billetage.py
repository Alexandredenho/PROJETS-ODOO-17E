from odoo import _, api, fields, models, tools 
from odoo.exceptions import UserError, ValidationError


class CaisseBilletage(models.TransientModel):
    _name = 'caisse.billetage'
    _description = 'Billetage'
    _rec_name = 'caisse_id'
    _check_company_auto = True

    caisse_id = fields.Many2one(
        comodel_name='account.caisse',
        string='Caisse',
        check_company=True
    )

    billetage_model_id = fields.Many2one(
        comodel_name='modele.billetage',
        string='Model de billetage',
        check_company=True
    )

    billetage_ids = fields.One2many(
        comodel_name='caisse.billetage.line',
        inverse_name='billetage_id',
        string='Linge de billetage',
    )

    montant_total = fields.Float(
        string="Montant total",
        compute="_compute_montant_total",
        store=True
    )

    balance = fields.Selection(
        selection=[('start', 'Solde initial'),
                   ('close', 'Solde final')
                   ],
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True,
        ondelete='restrict',
        default=lambda self: self.env.company
    )

    @api.onchange('billetage_model_id')
    def onchange_billetage_model_id(self):
        for rec in self:
            lines = []
            for line in rec.billetage_model_id.line_ids:
                vals =(0,0,{
                    'valeur':line.valeur,
                })
                lines.append(vals)
            
            rec.billetage_ids = lines

    def print_billetage(self):
        data ={}
        company_id = {
            "name": self.company_id.name,
            'logo': self.company_id.logo,
            "description": self.company_id.description,
            "street": self.company_id.street,
            "rccm": self.company_id.rccm,
            "vat": self.company_id.vat,
            "email": self.company_id.email,
            "nif": self.company_id.nif,
            "phone": self.company_id.phone,
            "numeroimpex": self.company_id.numeroimpex,
            'start_date':self.caisse_id.date_start.strftime('%d/%m/%Y %H:%M:%S'),
            'end_date':self.caisse_id.date_end.strftime('%d/%m/%Y %H:%M:%S'),
        }
        lines = []
        for line in self.billetage_ids:
            vals = {
                'nombre': line.nombre,
                'valeur': line.valeur,
                'montant': line.montant,
            }
            lines.append(vals)
        data['lines'] = lines
        data['montant_total']= self.montant_total
        data['company_id']= company_id
        data['caisse_name']= self.caisse_id.reference,
        data['balance'] = 'Ouverture' if self.balance == 'start' else 'Fermeture'
        data['type_caisse'] = self.caisse_id.type_id.name
        data['caissier'] =  self.caisse_id.user_id.name
        return self.env.ref('th_caisse_externe.th_report_billetage').report_action(self, data=data)


    @api.depends('billetage_ids')
    def _compute_montant_total(self):
        for record in self:
            record.montant_total = sum(line.montant for line in record.billetage_ids)

    @api.onchange('caisse_id')
    def onchange_caisse_id(self):
        if self.caisse_id:
            lines = []
            for line in self.caisse_id.billetage_ids:
                if line.balance == self.balance:
                    
                    vals = (0, 0, {
                        'nombre': line.nombre,
                        'valeur': line.valeur,
                        'montant': line.montant,
                        'balance': line.balance,
                        'caisse_id': self.caisse_id.id,
                        'company_id': self.company_id.id,
                    })
                    lines.append(vals)
            self.billetage_ids = [(5, 0, 0)]
            self.billetage_ids = lines

    def confirm(self):
        lines = []
        for line in self.billetage_ids:
            vals = (0, 0, {
                'nombre': line.nombre,
                'valeur': line.valeur,
                'balance': self.balance,
                'montant': line.montant,
                'caisse_id': self.caisse_id.id,
                'company_id': self.company_id.id,
            })
            lines.append(vals)
        for line in self.caisse_id.billetage_ids.filtered(lambda b: b.balance == self.balance):
                line.unlink()
        self.caisse_id.write({'billetage_ids': lines})
        if self.balance == "start":
            self.caisse_id.write({
                'solde_initial': self.montant_total
            })
        else:
            self.caisse_id.write({
                'solde_final': self.montant_total
            })


class CaisseBilletageLine(models.TransientModel):
    _name = 'caisse.billetage.line'
    _description = 'Linge de billetage'
    _check_company_auto = True

    nombre = fields.Float(string="Nombre de billet/pièce")
    valeur = fields.Float(string="Valeur")
    montant = fields.Float(string="Montant")

    caisse_id = fields.Many2one(
        comodel_name='account.caisse',
        string='Caisse',
        check_company=True
    )

    balance = fields.Selection(
        selection=[('start', 'Solde initial'),
                   ('close','Solde final')
                   ]
    )

    billetage_id = fields.Many2one(
        comodel_name='caisse.billetage',
        string='Model de billetage',
        check_company=True
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        copy=True, store=True, index=True, 
        ondelete='restrict',
        default=lambda self: self.env.company
    )

    @api.onchange('nombre','valeur')
    def onchange_nombre_valeur(self):
        for rec in self:
            rec.montant = rec.nombre * rec.valeur