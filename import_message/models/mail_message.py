# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    unique_code = fields.Char()
