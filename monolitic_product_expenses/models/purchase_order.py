# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    estimated_perc = fields.Float(
        string="Estimated Import Cost (%)",
    )
    total_expense = fields.Float(
        digits='Product Price',
        string="Import Expenses",
        readonly=True,
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        if not self.product_id:
            return res
        else:
            self.estimated_perc = self.product_id.categ_id.estimate_cost
        return res

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        res = super(PurchaseOrderLine, self)._compute_amount()

        for line in self:
            if line.product_id:
                line.total_expense = (
                    line.price_unit * line.product_qty
                    * line.estimated_perc / 100)

        return res

    # Add % estimated expenses to price_unit before create stock.move
    # Easier to override function
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit * (1 + line.estimated_perc / 100)

        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id,
                quantity=1.0, product=line.product_id,
                partner=line.order_id.partner_id
            )['total_excluded']

        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= (
                line.product_uom.factor / line.product_id.uom_id.factor)

        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, self.company_id,
                self.date_order or fields.Date.today(), round=False)

        return price_unit

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res.update({
            'total_expense': self.total_expense,
            'estimated_perc': self.estimated_perc,
            'real_perc': self.estimated_perc,
        })
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    doc_number = fields.Char(string='Nº Document')
