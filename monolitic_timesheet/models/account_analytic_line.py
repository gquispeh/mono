# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _order = 'date_time desc'

    date_time = fields.Datetime(
        default=fields.Datetime.now,
        copy=False,
    )

    @api.model
    def _eval_date(self, vals):
        if vals.get('date_time'):
            return dict(vals, date=fields.Date.to_date(vals['date_time']))
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(list(map(self._eval_date, vals_list)))

    def write(self, vals):
        return super().write(self._eval_date(vals))
