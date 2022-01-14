# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class CustomerPrevision(models.Model):
    _name = 'customer.prevision'
    _description = 'Model for managing previsions for customers'
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

            # current_year = int(date.today().year)
            # year = int(record.year)
            # if year < current_year - 1:
            #     raise ValidationError(_(
            #         'The year introduced must be equal or '
            #         'greater than %d ! ') % int(current_year - 1))

    @api.model
    def _default_initial_year(self):
        return int(date.today().year)

    def _default_monthly_prevision_amounts(self):
        return [(0, 0, {
            'month': month,
            'amount': 0.0,
            'amount_type': 'prevision',
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
    market_ids = fields.Many2many(
        comodel_name='monolitic.client.segmentation',
        compute='_compute_market_categ_ids',
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
    partner_id = fields.Many2one(
        string='Contact',
        comodel_name='res.partner',
        required=True,
    )
    lead_id = fields.Many2one(
        string='Lead/Oppn',
        comodel_name='crm.lead',
        required=True,
    )
    monthly_prevision_amount_ids = fields.One2many(
        string='Monthly Prevision Amounts',
        comodel_name='commercial.monthly.amount',
        inverse_name='customer_prevision_id',
        default=_default_monthly_prevision_amounts,
    )

    _sql_constraints = [(
        'year_commercial_uniq',
        'unique(year, market_segmentation_id, product_segmentation_id, '
        'user_id, lead_id)',
        'This customer has already a prevision for '
        'this year, this market segmentation, '
        'product segmentation and commercial !'
    )]

    def _create_new_commercial_target(self):
        commercial_target_vals = {
            'year': self.year,
            'user_id': self.user_id.id,
            'market_segmentation_id': self.market_segmentation_id.id,
            'product_segmentation_id': self.product_segmentation_id.id,
            'total_amount': 0,
        }
        self.user_id.sudo().write({
            'commercial_target_ids': [(0, 0, commercial_target_vals)]
        })

    '''
        Update fields to prevision lines on create for reporting
    '''
    @api.model
    def create(self, vals):
        res = super(CustomerPrevision, self).create(vals)
        for rec in res:
            if rec.year:
                rec.monthly_prevision_amount_ids.write({'year': rec.year})
            if rec.market_segmentation_id:
                rec.monthly_prevision_amount_ids.write({
                    'market_segmentation_id': rec.market_segmentation_id.id})
            if rec.product_segmentation_id:
                rec.monthly_prevision_amount_ids.write({
                    'product_segmentation_id': rec.product_segmentation_id.id})
            if rec.user_id:
                rec.monthly_prevision_amount_ids.write({
                    'user_id': rec.user_id.id})
            if rec.partner_id:
                rec.monthly_prevision_amount_ids.write({
                    'partner_id': rec.partner_id.id})

            # Check if a commercial target exists with these fields, if not,
            # create a new one with amounts to 0
            # if rec.market_segmentation_id:
            #     commercial_target_obj = self.env['commercial.target'].search([
            #         ('year', '=', rec.year),
            #         ('market_segmentation_id', '=', rec.market_segmentation_id.id),
            #         ('user_id', '=', rec.user_id.id),
            #     ])
            #     if not commercial_target_obj:
            #         rec._create_new_commercial_target()

        return res

    '''
        Update fields to prevision lines on write for reporting
    '''
    def write(self, vals):
        res = super(CustomerPrevision, self).write(vals)
        if 'year' in vals:
            self.monthly_prevision_amount_ids.write({'year': self.year})
        if 'market_segmentation_id' in vals:
            if self.market_segmentation_id:
                # Check if a commercial target exists with these fields,
                # if not, create a new one with amounts to 0
                commercial_target_obj = self.env['commercial.target'].search([
                    ('year', '=', self.year),
                    ('market_segmentation_id', '=',
                        self.market_segmentation_id.id),
                    ('user_id', '=', self.user_id.id),
                ])
                if not commercial_target_obj:
                    self._create_new_commercial_target()

            self.monthly_prevision_amount_ids.write({
                'market_segmentation_id': self.market_segmentation_id.id})
        if 'product_segmentation_id' in vals:
            self.monthly_prevision_amount_ids.write({
                'product_segmentation_id': self.product_segmentation_id.id})
        if 'user_id' in vals:
            self.monthly_prevision_amount_ids.write({
                'user_id': self.user_id.id})
        if 'partner_id' in vals:
            self.monthly_prevision_amount_ids.write({
                'partner_id': self.partner_id.id})
        return res

    def _get_target_coeficient(self):
        coef_user_partner = self.env['commercial.target.coeficient'].search([
            ('year', '=', self.year),
            ('user_id', '=', self.user_id.id),
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        if coef_user_partner:
            return coef_user_partner
        else:
            coef_partner = self.env['commercial.target.coeficient'].search([
                ('year', '=', self.year),
                ('partner_id', '=', self.partner_id.id)
            ], limit=1)
            if coef_partner:
                return coef_partner
            else:
                coef_user = self.env['commercial.target.coeficient'].search([
                    ('year', '=', self.year),
                    ('user_id', '=', self.user_id.id),
                ], limit=1)
                if coef_user:
                    return coef_user
                else:
                    coef_year = self.env[
                        'commercial.target.coeficient'].search([
                            ('year', '=', self.year),
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
                    'A target coeficient for this contact, commercial '
                    'and year could not be found. Please create one '
                    'before assigning prevision amounts.'))
            amount = rec.total_amount
            for month_prev in rec.monthly_prevision_amount_ids:
                month_prev.amount = (
                    amount * coef_obj.monthly_coef_amount_ids.filtered(
                        lambda x: x.month == month_prev.month).amount)

    @api.onchange('total_amount')
    def _onchange_total_amount(self):
        if not self.env.context.get("skip_onchange"):
            self._calculate_monthly_amounts()

    @api.onchange('monthly_prevision_amount_ids')
    def _onchange_month_prevision_amounts(self):
        for rec in self:
            total_amount = sum(rec.monthly_prevision_amount_ids.mapped('amount'))
            rec.total_amount = total_amount
        self.env.context = self.with_context(skip_onchange=True).env.context

    @api.depends('partner_id')
    def _compute_market_categ_ids(self):
        domain = [('level_parents', '>=', 2)]
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.segmentation_ids:
                    domain = [(
                        'id', 'in', self.partner_id.segmentation_ids.ids)]

            market_segmentation_obj = self.env[
                'monolitic.client.segmentation'].search(domain)
            rec.market_ids = market_segmentation_obj.ids
