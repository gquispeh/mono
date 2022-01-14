from odoo import api, fields, models
from datetime import datetime


class CurrencyRates(models.AbstractModel):
    _name = 'currency.rates.mixing'
    _description = 'Add rates to currencies to the inherit model'

    rate = fields.Float(
        'Rate',
        digits=(12, 6),
        tracking=True,
        default=1.00,
    )
    different_agreement_rate = fields.Boolean(
        string='Different agreement rate'
    )
    is_rate_editable = fields.Boolean(compute='_compute_is_rate_editable')

    def _compute_is_rate_editable(self):
        for rec in self:
            if self.env.user.has_group(
                'monolitic_currency_rates.change_rate_account_moves'
            ):
                rec.is_rate_editable = True
            else:
                rec.is_rate_editable = False

    @api.onchange('currency_id')
    def _onchange_rates_currency_id(self, date):
        if not date:
            date = datetime.now().date()
        if (self.currency_id and
                self.currency_id != self.env.company.currency_id):
            self.rate = self.currency_id.rate
        else:
            self.rate = 1.00
