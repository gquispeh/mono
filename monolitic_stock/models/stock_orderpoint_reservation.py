from odoo import fields, models
# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class StockOrderpointReservation(models.Model):
    _name = 'stock.orderpoint.reservation'
    _description = 'Model for make reordering rule per client product units'
    _rec_name = "id"

    partner_id = fields.Many2one(comodel_name='res.partner')
    min_quantity = fields.Integer()
    orderpoint_id = fields.Many2one(
        comodel_name='stock.warehouse.orderpoint')
    product_id = fields.Many2one(related="orderpoint_id.product_id")
