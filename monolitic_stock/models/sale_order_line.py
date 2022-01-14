# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    number = fields.Integer(
        compute='_compute_get_number',
        store=True,
    )

    @api.depends('sequence', 'order_id')
    def _compute_get_number(self):
        for order in self.mapped('order_id'):
            number = 1
            for line in order.order_line:
                line.number = number
                number += 1
