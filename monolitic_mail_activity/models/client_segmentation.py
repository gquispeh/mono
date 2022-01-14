# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ClientSegmentation(models.Model):
    _inherit = 'monolitic.client.segmentation'

    application_ids = fields.One2many(
        comodel_name='mail.activity', compute="_compute_applications_ids")

    def _compute_applications_ids(self):
        mail_obj = self.env['mail.activity']
        for rec in self:
            ids = mail_obj.search([('application_id', 'in', rec.id)]).ids
            rec.application_ids = [(6, 0, ids)]
