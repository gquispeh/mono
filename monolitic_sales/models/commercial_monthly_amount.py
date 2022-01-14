# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class CommercialMonthlyAmount(models.Model):
    _name = 'commercial.monthly.amount'
    _description = 'Model for managing Commercial Monthly Amounts'
    _rec_name = 'month'

    month = fields.Selection(
        string='Month',
        selection=[
            ('1', 'January'), ('2', 'February'), ('3', 'March'),
            ('4', 'April'), ('5', 'May'), ('6', 'June'),
            ('7', 'July'), ('8', 'August'), ('9', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ],
        required=True,
    )
    amount = fields.Float(
        string='Amount',
        digits='Target Coeficient',
        required=True,
    )
    prevision_amount = fields.Float(
        string='Prevision Amount',
        digits='Target Coeficient',
        compute="_compute_amounts",
    )
    diff_amount = fields.Float(
        string='Difference target vs prevision',
        digits='Target Coeficient',
        compute="_compute_amounts",
    )
    invoiced_amount = fields.Float(
        string='Invoiced amount',
        digits='Target Coeficient',
        compute="_compute_amounts",
    )
    menf_amount = fields.Float(
        string='MENF amount',
        digits='Target Coeficient',
        compute="_compute_amounts",
    )
    real_diff_amount = fields.Float(
        string='Real difference amount',
        digits='Target Coeficient',
        compute="_compute_amounts",
    )
    amount_type = fields.Selection(
        string='Amount Type',
        selection=[
            ('target', 'Target'),
            ('prevision', 'Prevision'),
            ('coeficient', 'Coeficient'),
        ],
        required=True,
    )

    # Related fields to be set from its parents
    commercial_target_id = fields.Many2one(
        string='Commercial Target',
        comodel_name='commercial.target',
        ondelete='cascade',
        index=True,
        copy=False,
    )
    customer_prevision_id = fields.Many2one(
        string='Customer Prevision',
        comodel_name='customer.prevision',
        ondelete='cascade',
        index=True,
        copy=False,
    )
    target_coeficient_id = fields.Many2one(
        string='Target Coeficient',
        comodel_name='commercial.target.coeficient',
        ondelete='cascade',
        index=True,
        copy=False,
    )
    year = fields.Char(
        string='Year',
    )
    market_segmentation_id = fields.Many2one(
        string='Market segmentation',
        comodel_name='monolitic.client.segmentation',
    )
    user_id = fields.Many2one(
        string='Commercial',
        comodel_name='res.users',
        index=True,
    )
    product_segmentation_id = fields.Many2one(
        string='Product segmentation',
        comodel_name='product.category',
    )
    partner_id = fields.Many2one(
        string='Contact',
        comodel_name='res.partner',
        index=True,
    )

    def last_day_of_month(self, month, year):
        if month == 12:
            return datetime(year, month, 31)
        previous_date = datetime(year, month + 1, 1)
        return previous_date - timedelta(days=1)

    def _compute_amounts(self):
        for rec in self:
            # Compute prevision amounts
            prevision_lines = self.env['commercial.monthly.amount'].search([
                ('year', '=', rec.year),
                ('month', '=', rec.month),
                ('user_id', '=', rec.user_id.id),
                ('market_segmentation_id', '=', rec.market_segmentation_id.id),
                ('amount_type', '=', 'prevision'),
            ]).mapped('amount')
            prevision_amount = sum(prevision_lines)
            rec.prevision_amount = prevision_amount
            rec.diff_amount = rec.amount - prevision_amount

            # Compute real amounts
            first_day_month = datetime(int(rec.year), int(rec.month), 1)
            last_day_month = self.last_day_of_month(
                int(rec.month), int(rec.year))
            lines_obj = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', first_day_month),
                ('order_id.date_order', '<=', last_day_month),
                ('state', '=', 'sale'),
                ('user_id', '=', rec.user_id.id),
                ('client_segmentation_id', '=', rec.market_segmentation_id.id),
            ])
            invoiced_amount = 0.00
            invoiced_lines_obj = lines_obj.filtered(lambda x: x.invoice_lines)
            for inv_line in invoiced_lines_obj:
                invoiced_amount += sum(
                    inv_line.invoice_lines.filtered(
                        lambda x: x.invoice_id.state == 'open'
                    ).mapped('price_subtotal'))
            menf_amount = sum(lines_obj.filtered(
                lambda x: not x.invoice_lines and
                x.qty_delivered == x.product_qty).mapped('price_subtotal'))

            rec.invoiced_amount = invoiced_amount
            rec.menf_amount = menf_amount
            rec.real_diff_amount = rec.amount - (invoiced_amount + menf_amount)

    #  Inherit read_group to calculate the sum of the non-stored fields,
    #  as it is not automatically done anymore through the XML.
    @api.model
    def read_group(
            self, domain, fields, groupby, offset=0,
            limit=None, orderby=False, lazy=True):
        res = super(CommercialMonthlyAmount, self).read_group(
            domain, fields, groupby, offset=offset,
            limit=limit, orderby=orderby, lazy=lazy)
        fields_list = [
            'prevision_amount', 'diff_amount', 'invoiced_amount',
            'menf_amount', 'real_diff_amount']
        if any(x in fields for x in fields_list):
            for r in res:
                if r.get('__domain'):
                    lines = self.search(r['__domain'])
                    prevision_amount = 0.00
                    diff_amount = 0.00
                    invoiced_amount = 0.00
                    menf_amount = 0.00
                    real_diff_amount = 0.00
                    for line in lines:
                        prevision_amount += line.prevision_amount
                        diff_amount += line.diff_amount
                        invoiced_amount += line.invoiced_amount
                        menf_amount += line.menf_amount
                        real_diff_amount += line.real_diff_amount
                    r['prevision_amount'] = prevision_amount
                    r['diff_amount'] = diff_amount
                    r['invoiced_amount'] = invoiced_amount
                    r['menf_amount'] = menf_amount
                    r['real_diff_amount'] = real_diff_amount
        return res

    def action_open_commercial_target_form(self):
        return {
            'name': _('Commercial Target'),
            'res_model': 'commercial.target',
            'type': 'ir.actions.act_window',
            'res_id': self.env.context.get('target_id'),
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    def action_open_prevision_amount_tree(self):
        prevision_amount_ids = self.env['commercial.monthly.amount'].search([
            ('year', '=', self.year),
            ('month', '=', self.month),
            ('user_id', '=', self.user_id.id),
            ('market_segmentation_id', '=', self.market_segmentation_id.id),
            ('amount_type', '=', 'prevision'),
        ]).ids

        return {
            'name': _('Sales Previsions'),
            'res_model': 'commercial.monthly.amount',
            'type': 'ir.actions.act_window',
            'res_id': self.env.context.get('target_id'),
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'monolitic_sales.sales_prevision_amount_tree_view').id,
            'target': 'current',
            'domain': [('id', 'in', prevision_amount_ids)]
        }

    def action_open_invoiced_amount_tree(self):
        first_day_month = datetime(int(self.year), self.month, 1)
        last_day_month = self.last_day_of_month(
            int(self.month), int(self.year))
        lines_obj = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', first_day_month),
            ('order_id.date_order', '<=', last_day_month),
            ('state', '=', 'sale'),
            ('user_id', '=', self.user_id.id),
            ('client_segmentation_id', '=', self.market_segmentation_id.id),
        ])
        invoiced_lines_ids = lines_obj.filtered(
            lambda x: x.invoice_lines.invoice_id.state == 'open').ids

        return {
            'name': _('Invoiced Amount Lines'),
            'res_model': 'sale.order.line',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'sale_order_line_input.view_sales_order_line_input_tree').id,
            'target': 'current',
            'domain': [('id', 'in', invoiced_lines_ids)]
        }

    def action_open_menf_amount_tree(self):
        first_day_month = datetime(int(self.year), self.month, 1)
        last_day_month = self.last_day_of_month(
            int(self.month), int(self.year))
        lines_obj = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', first_day_month),
            ('order_id.date_order', '<=', last_day_month),
            ('state', '=', 'sale'),
            ('user_id', '=', self.user_id.id),
            ('client_segmentation_id', '=', self.market_segmentation_id.id),
        ])
        menf_lines_ids = lines_obj.filtered(
                lambda x: not x.invoice_lines and
                x.qty_delivered == x.product_qty).ids

        return {
            'name': _('MENF Amount Lines'),
            'res_model': 'sale.order.line',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'sale_order_line_input.view_sales_order_line_input_tree').id,
            'target': 'current',
            'domain': [('id', 'in', menf_lines_ids)]
        }

    def action_open_partner_oppns(self):
        opportunities_ids = self.env['crm.lead'].search([
            ('partner_id', '=', self.env.context.get('partner_id')),
            ('type', '=', 'opportunity'),
        ]).ids
        oppn_tree = self.env.ref('crm.crm_case_tree_view_oppor')
        return {
            'name': _('Opportunities'),
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'res_id': self.env.context.get('target_id'),
            'view_mode': 'tree,kanban,graph,pivot,form,calendar,activity',
            'views': [(oppn_tree.id, 'tree')],
            'target': 'current',
            'domain': [('id', 'in', opportunities_ids)]
        }
