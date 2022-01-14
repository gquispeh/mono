# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class ProductStockMixin(models.AbstractModel):
    _name = 'product.stock.mixin'
    _description = "Product Stock Mixin"

    def get_data_actual_stock(self):
        data = {}
        product_id = self.product_id
        data.setdefault(product_id, {})
        SaleOrderLine = self.env['sale.order.line']
        so = SaleOrderLine.search([
            ('product_id', '=', product_id.id),
            ('state', '!=', 'draft')])
        data[product_id].update({'so': so})
        product_prod_ids = self.env['mrp.production'].search([
            ('move_raw_ids.product_id', '=', product_id.id),
            ('state', '!=', 'cancel'),
            ('origin', '!=', False)
        ])
        data[product_id].update({'mo': product_prod_ids.mapped(
            'move_raw_ids'
        ).filtered(
            lambda l: l.product_id == product_id
        )})
        reserved_availability = sum(
            product_prod_ids.mapped('move_raw_ids').filtered(
                lambda m: m.product_id == product_id
            ).mapped('reserved_availability')
        )
        sale_prod_ids = SaleOrderLine.search([
            (
                'product_id', 'in',
                product_prod_ids.mapped('product_id').ids
            ),
            (
                'order_id.name', 'in',
                product_prod_ids.mapped('origin')
            ),
            ('state', '!=', 'draft')
        ])
        data[product_id].update({'sale_mo': sale_prod_ids})
        po = self.env['purchase.order.line'].search([
            ('product_id', '=', product_id.id),
            ('state', '!=', 'draft')])
        data[product_id].update({'po': po})
        data[product_id].update(
            {'reserved_availability': reserved_availability}
        )
        return data
