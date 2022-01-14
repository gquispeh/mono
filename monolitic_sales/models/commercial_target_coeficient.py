# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class CommercialTargetCoeficient(models.Model):
    _name = 'commercial.target.coeficient'
    _description = 'Model for managing Commercial Target Coeficients'
    _rec_name = 'year'

    MONTH_LIST = [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
    ]

    @api.constrains('year')
    def _check_year(self):
        for record in self:
            try:
                int(record.year)
            except Exception:
                raise ValidationError(_('Please write a valid year ! '))

            # current_year = int(date.today().year)
            # year = int(record.year)
            # if year < current_year - 1:
            #     raise ValidationError(_(
            #         'The year introduced must be equal or '
            #         'greater than %d ! ') % int(current_year - 1))

    @api.model
    def _default_initial_year(self):
        return int(date.today().year)

    def _default_monthly_coef_amounts(self):
        return [(0, 0, {
            'month': month,
            'amount': 0.0,
            'amount_type': 'coeficient',
        }) for month in self.MONTH_LIST]

    year = fields.Char(
        string='Year',
        default=_default_initial_year,
        required=True,
    )
    user_id = fields.Many2one(
        string='Commercial',
        comodel_name='res.users',
        domain="[('is_commercial', '=', True)]",
    )
    partner_id = fields.Many2one(
        string='Contact',
        comodel_name='res.partner',
    )
    monthly_coef_amount_ids = fields.One2many(
        string='Monthly Coeficient Amounts',
        comodel_name='commercial.monthly.amount',
        inverse_name='target_coeficient_id',
        default=_default_monthly_coef_amounts,
        copy=True,
    )

    _sql_constraints = [
        ('year_commercial_uniq', 'unique(year, user_id)',
            'A commercial can only have one target coeficient per year!'),
    ]

    '''
        Check if total coeficient equals 1 on create
    '''
    @api.model
    def create(self, vals):
        res = super(CommercialTargetCoeficient, self).create(vals)

        if 'monthly_coef_amount_ids' in vals:
            total_coeficient = sum(res.monthly_coef_amount_ids.mapped('amount'))
            if round(total_coeficient, 3) != 1:
                raise ValidationError(_(
                    'The total coeficient value must be equal to 1 !'))

        return res

    '''
        Check if total coeficient equals 1 on write
    '''
    def write(self, vals):
        res = super(CommercialTargetCoeficient, self).write(vals)

        for coef in self:
            if 'monthly_coef_amount_ids' in vals:
                total_coeficient = sum(
                    coef.monthly_coef_amount_ids.mapped('amount'))
                if round(total_coeficient, 3) != 1:
                    raise ValidationError(_(
                        'The total coeficient value must be equal to 1 !'))

        return res
