# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'currency.rates.mixing']

    purchase_currency_id = fields.Many2one(
        string='Purchase Currency',
        comodel_name='res.currency',
    )
    parity = fields.Float(
        string='Parity',
        default=1.0,
        digits=(12, 6),
    )

    @api.onchange('purchase_currency_id')
    def _onchange_purchase_currency(self):
        for rec in self:
            if rec.purchase_currency_id:
                if rec.purchase_currency_id.rate == rec.currency_id:
                    rec.parity = 1.0
                else:
                    rec.parity = rec.purchase_currency_id._get_conversion_rate(rec.purchase_currency_id, rec.currency_id, rec.company_id, date.today())
            else:
                rec.parity = 1.0

    @api.onchange('currency_id', 'date_order')
    def _onchange_rates_currency_id(self):
        # Update currency_rate
        if not self.currency_id:
            return super(SaleOrder, self)._onchange_rates_currency_id(
                self.date_order)
        if self.currency_id.id != self.env.user.company_id.currency_id.id:
            currency_rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.currency_id.id),
                ('name', '=', self.date_order)])
            if not currency_rate:
                self.rate = 1.0
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _(
                            'There is no currency rate for the date: %s' %
                            self.date_order.date())
                    }
                    }
        return super(
            SaleOrder, self)._onchange_rates_currency_id(self.date_order)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.different_agreement_rate:
            res.update({
                'rate': self.rate,
                'different_agreement_rate': self.different_agreement_rate,
            })
        return res

    # def _create_invoices(self, grouped=False, final=False, date=None):
    #     for rec in self:
    #         ctx = rec._context.copy()
    #         if rec.different_agreement_rate:
    #             ctx.update({'rate': rec.rate})
    #         res = super(SaleOrder, rec.with_context(ctx))._create_invoices(
    #             grouped, final, date)
    #     return res

    # TODO: FIX ME
    def _create_invoices(self, grouped=False, final=False, date=None):
        for rec in self:
            if rec.different_agreement_rate:
                self.env.context = dict(self.env.context)
                self.env.context.update({'rate': rec.rate})
        return super(SaleOrder, self)._create_invoices(grouped, final, date)
