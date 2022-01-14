# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class CommercialTarget(models.Model):
    _name = 'commercial.target'
    _description = 'Model for managing targets for commercials'
    _order = 'year desc'

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

            current_year = int(date.today().year)
            year = int(record.year)
            if year < current_year - 1:
                raise ValidationError(_(
                    'The year introduced must be equal or '
                    'greater than %d ! ') % int(current_year - 1))

    @api.model
    def _default_initial_year(self):
        return int(date.today().year)

    def _default_monthly_target_amounts(self):
        return [(0, 0, {
            'month': month,
            'amount': 0.0,
            'amount_type': 'target',
        }) for month in self.MONTH_LIST]

    year = fields.Char(
        string='Year',
        default=_default_initial_year,
        required=True,
    )
    market_segmentation_id = fields.Many2one(
        string='Market segmentation',
        comodel_name='monolitic.client.segmentation',
    )
    product_segmentation_id = fields.Many2one(
        string='Product segmentation',
        comodel_name='product.category',
    )
    total_amount = fields.Float(
        string='Total Amount',
        required=True,
    )
    user_id = fields.Many2one(
        string='Commercial',
        comodel_name='res.users',
        required=True,
    )
    # We need a second res.users field for a better search on onchange
    related_user = fields.Many2one(
        string='Related User',
        comodel_name='res.users',
        required=True,
    )
    monthly_target_amount_ids = fields.One2many(
        string='Monthly Target Amounts',
        comodel_name='commercial.monthly.amount',
        inverse_name='commercial_target_id',
        default=_default_monthly_target_amounts,
    )

    _sql_constraints = [(
        'year_commercial_uniq',
        'unique(year, market_segmentation_id, product_segmentation_id, '
        'user_id)',
        'This customer has already a prevision for '
        'this year, this market segmentation, '
        'product segmentation and commercial !'
    )]

    @api.constrains('user_id')
    def check_user_id_commercial(self):
        for record in self:
            if record.user_id != record.related_user:
                raise ValidationError(_(
                    "You cannot set a different commercial than this user !"))

    '''
        Update fields to target lines on create for reporting
    '''
    @api.model
    def create(self, vals):
        res = super(CommercialTarget, self).create(vals)
        for rec in res:
            if rec.year:
                rec.monthly_target_amount_ids.write({'year': rec.year})
            if rec.market_segmentation_id:
                rec.monthly_target_amount_ids.write({
                    'market_segmentation_id': rec.market_segmentation_id.id})
            if rec.product_segmentation_id:
                rec.monthly_target_amount_ids.write({
                    'product_segmentation_id': rec.product_segmentation_id.id})
            if rec.user_id:
                rec.monthly_target_amount_ids.write({'user_id': rec.user_id.id})
        return res

    '''
        Update fields to target lines on write for reporting
    '''
    def write(self, vals):
        res = super(CommercialTarget, self).write(vals)

        if 'year' in vals:
            self.monthly_target_amount_ids.write({'year': self.year})
        if 'market_segmentation_id' in vals:
            self.monthly_target_amount_ids.write({
                'market_segmentation_id': self.market_segmentation_id.id})
        if 'product_segmentation_id' in vals:
            self.monthly_target_amount_ids.write({
                'product_segmentation_id': self.product_segmentation_id.id})
        if 'user_id' in vals:
            self.monthly_target_amount_ids.write({'user_id': self.user_id.id})
        return res

    def _get_target_coeficient(self):
        coef_user = self.env['commercial.target.coeficient'].search([
            ('year', '=', self.year),
            ('user_id', '=', self.user_id.id),
        ], limit=1)
        if coef_user:
            return coef_user
        else:
            coef_year = self.env['commercial.target.coeficient'].search([
                ('year', '=', self.year)
            ], limit=1)
            if coef_year:
                return coef_year
            else:
                return False

    def _calculate_monthly_amounts(self):
        for rec in self:
            coef_obj = rec._get_target_coeficient()
            if not coef_obj:
                raise ValidationError(_(
                    'A target coeficient for this year or commercial '
                    'could not be found. Please create one before '
                    'assigning target amounts.'))

            amount = rec.total_amount
            for month_target in rec.monthly_target_amount_ids:
                month_target.amount = (
                    amount * coef_obj.monthly_coef_amount_ids.filtered(
                        lambda x: x.month == month_target.month).amount)

    @api.onchange('total_amount')
    def _onchange_total_amount(self):
        if not self.env.context.get("skip_onchange"):
            self._calculate_monthly_amounts()

    @api.onchange('monthly_target_amount_ids')
    def _onchange_month_target_amounts(self):
        for rec in self:
            total_amount = sum(rec.monthly_target_amount_ids.mapped('amount'))
            rec.total_amount = total_amount
        self.env.context = self.with_context(skip_onchange=True).env.context
