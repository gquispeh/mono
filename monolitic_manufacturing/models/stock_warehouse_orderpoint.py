from odoo import api, fields, models, _
# Copyright 2022 Albert Farrés <albert.farres@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError, UserError

class WarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'
    
    @api.model
    def create(self, vals):
        if vals.get("product_id", False):
            product = self.env['product.product'].browse(vals['product_id'])
            if product.bom_count > 0:
                raise UserError(
                    _("You cannot create a stock warehouse orderpoint on a product with material lists!")
                )
        return super(WarehouseOrderpoint, self).create(vals)
