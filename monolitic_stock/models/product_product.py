# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_customer_code(self, partner_id):
        for rec in self:
            rec.ensure_one()
            if partner_id.parent_id:
                partner_id = partner_id.parent_id

            customer_ids = rec.customer_ids.filtered(
                lambda x: x.name.id == partner_id.id)
            customer_product = customer_ids.filtered(
                lambda x: x.product_id.id == rec.id)
            if not customer_product:
                customer_product = customer_ids.filtered(
                    lambda x: not x.product_id)
            return customer_product.product_code if customer_product else ""
