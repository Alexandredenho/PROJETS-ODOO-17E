from odoo import _, api, fields, models, tools 
from odoo.exceptions import UserError, ValidationError

class CashReportWizard(models.TransientModel):

    _name = 'cash.report.wizard'
    _check_company_auto = True
    _description = "Rapport d'opération de caisse"
    
    caise_ids = fields.Many2many(
        comodel_name='account.caisse'
    )

    def print_report(self):
        data = {}
        company_id = self.env.company
        company_vals = {
            'logo': company_id.logo,
            'name': company_id.name,
            'description': company_id.description,
            'street': company_id.street,
            'rccm': company_id.rccm,
            'vat': company_id.vat,
            'email': company_id.email,
            'nif': company_id.nif,
            'phone': company_id.phone,
            'numeroimpex': company_id.numeroimpex,
        }
   
        caisse_list = []
        for caisse in self.caise_ids:
            total_entree = 0
            total_sortie = 0
            operations_list = []
            for operation in caisse.operation_ids:
                if operation.currency_amount > 0:
                    total_entree += operation.currency_amount
                else:
                    total_sortie += operation.currency_amount
                vals= {
                    'reference': operation.reference,
                    'date': operation.date.strftime('%d/%m/%y %H:%M:%S'),
                    'libelle': operation.libelle,
                    'partner_id': operation.partner_id.name,
                    'currency_amount': operation.currency_amount,
                    'beneficiaire': operation.beneficiaire,
                    'note': operation.note,
                    'categorie_id': operation.categorie_id.name,
                    'analytique': operation.analitic_account_id.display_name,
                    'full_name':operation.full_name,
                }
                operations_list.append(vals)
            caisse_vals ={
                'reference':caisse.reference,
                'start_date':caisse.date_start.strftime('%d/%m/%Y %H:%M:%S'),
                'end_date':caisse.date_end.strftime('%d/%m/%Y %H:%M:%S'),
                'total_entree':abs(total_entree),
                'total_sortie':abs(total_sortie),
                'solde_initial':abs(caisse.solde_initial),
                'solde_final':abs(caisse.solde_final),
                'operations_list':operations_list,
                'type_caisse' : caisse.type_id.name,
                'devise':caisse.currency_id.name,
                'caissier':caisse.user_id.name,
            }
            caisse_list.append(caisse_vals)

        data['caisse_list'] = caisse_list
        data['company_id'] = company_vals
        return self.env.ref('th_caisse_externe.th_caisse_externe_detail_report').report_action(self, data=data)