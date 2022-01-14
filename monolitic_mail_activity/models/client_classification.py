# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ClientClassification(models.Model):
    _inherit = 'monolitic.client.classification'

    mail_activity_ids = fields.One2many(
        comodel_name='mail.activity', inverse_name='classification_id')
