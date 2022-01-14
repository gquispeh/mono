# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    description = fields.Text('Description')
    difference = fields.Integer(
        compute='_compute_difference',
        store=True,
        digits='Product Unit of Measure'
    )

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_difference_qty(self):
        for record in self:
            record.difference = record.product_qty - record.theoretical_qty

