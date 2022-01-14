
from odoo import fields, models, api,  _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    client_segmentation_id = fields.Many2one(
        string='Market segmentation',
        comodel_name='monolitic.client.segmentation',
    )
    product_segmentation_id = fields.Many2one(
        string='Product segmentation',
        comodel_name='product.category',
    )
    pricelist_name = fields.Char(string='Pricelist Name', readonly=True)
    pricelist_price = fields.Float(
        string='Pricelist Price',
        digits='Product Price',
        readonly=True,
    )
    pricelist_date_start = fields.Datetime('Start Date', readonly=True)
    pricelist_date_end = fields.Datetime('End Date', readonly=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Commercial",
        related='move_id.user_id',
    )
    difference = fields.Float(
        compute="_compute_difference",
        store=True,
        digits='Product Price',
    )

    @api.depends('price_subtotal')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.price_subtotal - rec.pricelist_price
