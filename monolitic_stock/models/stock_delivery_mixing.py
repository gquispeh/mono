# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockDeliveryMixing(models.AbstractModel):
    _name = 'stock.delivery.mixing'
    _description = 'Abstract Model for add extra info in deliveries'

    delivery_time = fields.Char(string='Delivery Time')
    number_lumps = fields.Integer()
    delivery_conditions = fields.Many2one(
        comodel_name='stock.delivery.condition',
        string='Delivery carrier',
    )


class StockDeliveryConditions(models.Model):
    _name = 'stock.delivery.condition'
    _description = "Stock Delivery Condition Model"

    name = fields.Char()
    description = fields.Text()
