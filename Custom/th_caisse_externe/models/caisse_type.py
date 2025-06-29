from odoo import _, api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class TypeCaisse(models.Model):
    _name = 'type.caisse'
    _check_company_auto = True
    _description = 'Type de caisse'

    name = fields.Char(string="Nom")
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain=[('type', '=', 'cash')], check_company=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
    )
    solde_caisse = fields.Float(string="Solde caisse")
    seuil_maximal = fields.Float(string="Seuil maximal de la caisse")
    auto_post = fields.Boolean(string="Comptabiliser automatiquement les écritures comptables", default=True)
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
    )
    color = fields.Integer(string="Couleur")
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        copy=True, store=True, index=True,
        ondelete='restrict',
        default=lambda self: self.env.company.id
    )

    @api.model
    def create(self, values):
        result = super().create(values)
        vals = {
            'name': values['name'],
            'code': values['name'].replace(' ', '_'),
            'active': True,
            'prefix': values['name'].replace(' ', '_') + '_',
            'padding': 3,
            'number_next': 1,
            'number_increment': 1,
            'type_cassie_id': result.id,
        }

        self.env['ir.sequence'].create(vals)
        return result

    def write(self, values):
        res = super().write(values)
        if 'name' in values:
            sequence = self.env['ir.sequence'].search([('type_cassie_id', '=', self.id)])
            if sequence:
                sequence.write({
                    'name': values['name'],
                    'code': values['name'].replace(' ', '_'),
                })
            else:
                vals = {
                    'name': values['name'],
                    'code': values['name'].replace(' ', '_'),
                    'active': True,
                    'prefix': values['name'].replace(' ', '_') + '_',
                    'padding': 3,
                    'number_next': 1,
                    'number_increment': 1,
                    'type_cassie_id': self.id,
                }
                self.env['ir.sequence'].create(vals)
        return res

    def liste_des_operation(self):
        if self.env.user.id == self.user_id.id:
            return {
                'name': ('Opérations de ' + self.name),
                'domain': [('type_id', '=', self.id)],
                'res_model': 'account.caisse',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }
        else:
            raise UserError(_('Vous n\'etes pas autorisé à acceder à cette caisse !'))
