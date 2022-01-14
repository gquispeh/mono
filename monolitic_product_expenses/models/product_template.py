# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountIntrastatCode(models.Model):
    _inherit = 'account.intrastat.code'

    rate = fields.Float(
        string='Cost percentage (%)',
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ecoraee_active = fields.Boolean(string='Ecoraee Expense')
