from odoo import fields, models, api
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.state_id:
                    rec.commercial_zone_id = \
                        rec.partner_id.state_id.commercial_zone_id


class StockMove(models.Model):
    _inherit = 'stock.move'

    pricelist_name = fields.Char(string='Pricelist Name', readonly=True)
    pricelist_price = fields.Float(
        string='Pricelist Price',
        digits='Product Price',
        readonly=True,
    )
    pricelist_date_start = fields.Datetime('Start Date', readonly=True)
    pricelist_date_end = fields.Datetime('End Date', readonly=True)

    @api.model
    def create(self, values):
        res = super(StockMove, self).create(values)
        if res.sale_line_id:
            res.pricelist_name = res.sale_line_id.pricelist_name
            res.pricelist_price = res.sale_line_id.pricelist_price
            res.pricelist_date_start = res.sale_line_id.pricelist_date_start
            res.pricelist_date_end = res.sale_line_id.pricelist_date_end

        if res.sale_line_id.commitment_date:
            res.date = res.sale_line_id.commitment_date
            res.date_deadline = res.sale_line_id.commitment_date
        return res
