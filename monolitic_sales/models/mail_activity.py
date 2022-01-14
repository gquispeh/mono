# Copyright Jordi Jané 2021 <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    seller_id = fields.Many2one(domain="[('is_commercial', '=', True)]")
