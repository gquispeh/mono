# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    organisation_ids = fields.One2many(
        comodel_name='mail.activity',
        inverse_name='organisation_id'
    )

    seller_ids = fields.One2many(
        comodel_name='mail.activity',
        inverse_name='seller_id'
    )

    represented_ids = fields.One2many(
        comodel_name='mail.activity',
        inverse_name='represented_id'
    )

    employee = fields.Boolean()

    def associated_activities(self):
        mail_activity_view_tree = self.env.ref(
            'monolitic_mail_activity.mail_activity_view_tree', False)
        mail_activity_view_form = self.env.ref(
            'mail_activity_board.mail_activity_view_form_board', False)
        return {
            'name': ('Tus actividades asociadas'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mail.activity',
            'views': [(mail_activity_view_tree.id, 'tree'),
                      (mail_activity_view_form.id, 'form')],
            'target': 'current',
            'domain': [
                '|',
                ('active', '=', False), ('active', '=', True),
                ('organisation_id', '=', self.id)
            ]
        }
