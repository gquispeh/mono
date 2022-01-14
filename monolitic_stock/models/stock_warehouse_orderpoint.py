from odoo import api, fields, models
# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError, UserError

class WarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    orderpoint_reservation_ids = fields.One2many(
        comodel_name='stock.orderpoint.reservation',
        inverse_name='orderpoint_id')

    security_stock = fields.Float(string='Security Stock')
    product_min_qty = fields.Float(compute="_compute_product_min_qty",
                                   store=True,
                                   required=False)

    @api.depends('orderpoint_reservation_ids', 'security_stock')
    def _compute_product_min_qty(self):
        for rec in self:
            reservations = sum(self.orderpoint_reservation_ids.
                               mapped('min_quantity'))
            rec.product_min_qty = rec.security_stock + reservations
            rec.product_max_qty = rec.security_stock + reservations
