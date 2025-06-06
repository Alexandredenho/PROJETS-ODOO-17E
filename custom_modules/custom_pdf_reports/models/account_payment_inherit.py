from odoo import fields, models, api


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    check_number = fields.Char(
        string='N° de chéque',
    )

    amount_received = fields.Float(
        string='Montant reçu',
    )

    amount_due = fields.Float(
        string='Montant dû',
        compute='compute_amount_due',
    )

    def action_print_payement_receipt(self):
        return self.env.ref('account.action_report_payment_receipt').report_action(self)

    @api.depends('amount_received', 'amount')
    def compute_amount_due(self):
        for payment in self:
            payment.amount_due = 0
            if payment.amount_received > 0 and payment.amount > 0:
                payment.amount_due = payment.amount_received - payment.amount if payment.amount_received >= payment.amount else 0




