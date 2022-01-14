from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "product.stock.mixin"]

    sn_prod = fields.Text(
        string='S/N Prod.',
    )

    def print_product_actual_stock_action(self):
        # return report_action
        action = self.env.ref(
            'monolitic_manufacturing.print_product_actual_stock_move'
        ).read()[0]
        return action
