from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    operation_ids = fields.Many2many('mrp.routing.workcenter',
        relation='mrp_routing_mrp_bom_rel',
        column1='bom_id',
        column2='routing_id',
        string='Operations', copy=True)

class MrpBomLine(models.Model):
    _name = "mrp.bom.line"
    _inherit = ["mrp.bom.line", "product.stock.mixin"]

    def print_product_actual_stock_action(self):
        # return report_action
        action = self.env.ref(
            'monolitic_manufacturing.print_product_actual_stock_bom').read()[0]
        return action
