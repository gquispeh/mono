from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    not_valued_picking = fields.Boolean(
        string='Not valued picking',
    )
    prohibited_partial_shippings = fields.Boolean(
        string='Prohibited partial shippings',
    )
    delivery_conditions_id = fields.Many2one(
        string='Delivery carrier',
        comodel_name='stock.delivery.condition',
    )
    carrier_id = fields.Many2one(
        string='Delivery conditions'
    )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.partner_id:
            self.not_valued_picking = self.partner_id.not_valued_picking
            self.prohibited_partial_shippings = \
                self.partner_id.prohibited_partial_shippings
            self.carrier_id = self.partner_id.property_delivery_carrier_id
            self.delivery_conditions_id = \
                self.partner_id.delivery_conditions_id
        return res
