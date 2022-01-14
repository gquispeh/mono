# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, fields

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'currency.rates.mixing']

    @api.onchange('currency_id')
    def _onchange_rates_currency_id(self):
        return super(PurchaseOrder, self)._onchange_rates_currency_id(
            self.date_order)

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        for rec in self:
            if rec.different_agreement_rate:
                res.update({
                    'rate': rec.rate,
                    'different_agreement_rate': rec.different_agreement_rate,
                })
        return res

    def action_create_invoice(self):
        ctx = self._context.copy()
        if self.different_agreement_rate:
            ctx.update({'rate': self.rate})
        return super(
            PurchaseOrder, self.with_context(ctx)).action_create_invoice()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    '''
        Override function due to reconversion of currency
    '''
    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res
