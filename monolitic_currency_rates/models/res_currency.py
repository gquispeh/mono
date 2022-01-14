from odoo import fields, models, api

import logging
_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    sell_margin = fields.Float(string="Margin For Sales", digits=(12, 6))
    purchase_margin = fields.Float(
        string="Margin For Purchases", digits=(12, 6))

    def _convert(self, from_amount, to_currency, company, date, round=True):
        self, to_currency = self or to_currency, to_currency or self
        if self._context.get('currency'):
            to_currency = self.env['res.currency'].browse(
                self._context['currency'])

        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"

        # apply conversion rate
        if self == to_currency and self.rate == self._context.get('rate'):
            to_amount = from_amount
        else:
            if self._context.get('rate'):
                rate = self._context.get('rate')
            else:
                rate = self._get_conversion_rate(
                    self, to_currency, company, date)
                rate = 1.0 / rate

            if self._context.get('compute_supplier_price'):
                rate -= self.purchase_margin
            elif (
                self._context.get('active_model') == 'purchase.order' or
                self._context.get('type') == 'in_invoice'
            ) or self._context.get('default_move_type') == 'in_invoice':
                rate -= self.purchase_margin
            elif (
                self._context.get('active_model') == 'sale.order' or
                self._context.get('type') == 'out_invoice'
            ) or self._context.get('default_move_type') == 'out_invoice':
                rate += self.sell_margin

            # Get inverse rate
            rate = 1.0 / rate
            to_amount = from_amount * rate

        return to_currency.round(to_amount) if round else to_amount
