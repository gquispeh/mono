# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'currency.rates.mixing']

    def action_move_create(self):
        for rec in self:
            ctx = rec._context.copy()
            ctx.update({'rate': rec.rate})
            super(AccountMove, rec.with_context(ctx)).action_move_create()
        return True

    @api.onchange('currency_id', 'date')
    def _onchange_rates_currency_id(self):
        ctx = self._context.copy()
        if not (self._context.get('no_update_rate') or self.fixed_rate or
                self.invoice_origin):
            if self.different_agreement_rate:
                ctx.update({
                    'rate': self.rate,
                })
            return super(
                AccountMove, self.with_context(ctx)
            )._onchange_rates_currency_id(self.date)

    @api.model
    def _get_payments_vals(self):
        ctx = self._context.copy()
        ctx.update({'rate': self.rate})
        return super(AccountMove, self.with_context(ctx)).\
            _get_payments_vals()

    @api.onchange('rate')
    def _onchange_rate(self):
        ctx = self._context.copy()
        if self.different_agreement_rate:
            ctx.update({
                'currency': self.currency_id.id,
                'rate': self.rate,
            })
            self.with_context(ctx)._onchange_currency()
