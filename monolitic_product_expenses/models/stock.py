# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    unit_cost = fields.Float(
        digits='Product Price',
    )


class StockMove(models.Model):
    _inherit = 'stock.move'

    price_unit = fields.Float(
        digits='Product Price',
    )

    # Add % estimated expenses to price_unit before updating price cost
    # Easier to override function
    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id and \
                self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit * (1 + line.estimated_perc / 100)

            # if line.taxes_id:
            #     price_unit = line.taxes_id.with_context(
            #         round=False).compute_all(
            #             price_unit, currency=line.order_id.currency_id,
            #             quantity=1.0)['total_excluded']

            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= (
                    line.product_uom.factor / line.product_id.uom_id.factor)

            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since
                # the move is still in assigned state.
                # However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, order.company_id,
                    fields.Date.context_today(self), round=False)

            return price_unit
        return super(StockMove, self)._get_price_unit()


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    price_unit = fields.Float(
        related='move_id.price_unit',
        digits='Product Price',
        copy=False,
    )
