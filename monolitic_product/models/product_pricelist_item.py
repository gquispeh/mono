# Copyright 2020 Daniel López <daniel.lopez@qubiq.es>
# License AGPL-3.0 or later (https: //www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    max_quantity = fields.Integer(
        string='Maximum quantity',
    )
    product_tmpl_id = fields.Many2one(
        check_company=False,
        domain=[('is_component', '=', False)])
    base = fields.Selection(
       selection_add=[("trade_margin", "Trade margin")],
       ondelete={"trade_margin": "set default"},
    )
    supplier_pricelist_price = fields.Float(
        compute="_compute_supplier_pricelist_price")
    logistic_price = fields.Float(compute="_compute_supplier_pricelist_price")
    margin = fields.Float(default=0.0)
    computed_price = fields.Float(
        string='Price', digits='Product Price',
        compute='_get_computed_formula_price',
    )

    def _get_computed_formula_price(self):
        for rec in self:
            if rec.fixed_price:
                rec.computed_price = rec.fixed_price
            else:
                if rec.product_tmpl_id:
                    rec.computed_price = rec._compute_price(0, 0, rec.product_tmpl_id)
                else:
                    rec.computed_price = 0.00

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for values in vals_list:
    #         if values.get('applied_on', False):
    #             if not values.get('product_tmpl_id') and values.get('base') == 'trade_margin':
    #                 raise UserError(_('You can only use trade margin for an especific product, please select it.'))
    #     return super(ProductPricelistItem, self).create(values)

    # def write(self, values):
    #     if not values.get('product_tmpl_id') and values.get('base') == 'trade_margin':
    #         raise UserError(_('You can only use trade margin for an especific product, please select it.'))
    #     return super(ProductPricelistItem, self).write(values)

    def _compute_price(self, price, price_uom, product, quantity=1.0, partner=False):
        res = super(ProductPricelistItem, self)._compute_price(price, price_uom, product, quantity=1.0, partner=False)
        if self.compute_price == 'formula' and self.base == 'trade_margin':
            price = (product.supplier_pricelist_price + product.logistic_price) / (1 - self.margin / 100)
            return price
        else:
            return res

    @api.onchange('product_tmpl_id')
    def _compute_supplier_pricelist_price(self):
        for rec in self:
            supplier_pricelist_price_list = []
            for pricelist in rec.product_tmpl_id.seller_ids:
                if rec.currency_id == pricelist.currency_id:
                    supplier_pricelist_price_list.append(pricelist.price)
                else:
                    price_converted = pricelist.currency_id._convert(
                        pricelist.price, rec.currency_id,
                        self.env.user.company_id, datetime.now())
                    supplier_pricelist_price_list.append(price_converted)

            if supplier_pricelist_price_list:
                rec.supplier_pricelist_price = max(
                    supplier_pricelist_price_list, key=lambda x: float(x))
            else:
                rec.supplier_pricelist_price = 0

            rec.logistic_price = (
                rec.supplier_pricelist_price * (
                    rec.product_tmpl_id.categ_id.estimate_cost / 100)
            )
