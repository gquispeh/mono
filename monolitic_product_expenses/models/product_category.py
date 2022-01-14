# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    estimate_cost = fields.Float(string='Estimate Import Cost')
