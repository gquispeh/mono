from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone')
    customer_prevision_ids = fields.One2many(
        string='Customer Previsions',
        comodel_name='customer.prevision',
        inverse_name="lead_id",
    )
    prevision_editable = fields.Boolean(
        compute='_compute_prevision_editable',
    )

    def _compute_prevision_editable(self):
        current_user = self.env.user
        sales_manager = self.env.ref('sales_team.group_sale_manager')
        # Change for customer service when groups are done
        customer_service = self.env.ref(
            'sales_team.group_sale_salesman_all_leads')
        for rec in self:
            if current_user in sales_manager.users:
                rec.prevision_editable = True
            elif current_user in customer_service.users:
                rec.prevision_editable = True
            elif current_user in rec.partner_id.user_id:
                rec.prevision_editable = True
            else:
                rec.prevision_editable = False

    def write(self, vals):
        res = super(CrmLead, self).write(vals)

        if 'customer_prevision_ids' in vals:
            for rec in self.customer_prevision_ids:
                if (
                    not rec.market_segmentation_id or
                    not rec.product_segmentation_id
                ):
                    raise ValidationError(_(
                        'Market and product segmnetation are required !'))

        if 'stage_id' in vals:
            if (
                self.expected_revenue == 0 and
                self.stage_id.required_planned_revenue
            ):
                raise ValidationError(_(
                    'The planned revenue must be above 0 on the next stage, '
                    'please update it before proceeding !'))

        return res

    @api.onchange('customer_prevision_ids')
    def _onchange_customer_prevision_ids(self):
        if self.customer_prevision_ids:
            if not self.user_id:
                raise ValidationError(_(
                    'You cannot add/modify a new sales prevision if the '
                    'Commercial field is empty !'))

            for rec in self.customer_prevision_ids:
                if not rec.market_segmentation_id:
                    self.env.user.notify_danger(
                        message=_('Market Segmentation field is not set!'))

        current_year = str(date.today().year)
        expected_revenue = sum(
            self.customer_prevision_ids.filtered(
                lambda x: x.year >= current_year).mapped('total_amount'))
        if expected_revenue == 0 and self.stage_id.required_planned_revenue:
            raise ValidationError(_(
                'The planned revenue must be above 0 on this stage !'))

        self.expected_revenue = expected_revenue

    @api.onchange('user_id')
    def _onchange_user_id(self):
        for rec in self:
            if rec.user_id:
                rec.customer_prevision_ids.write({
                    'user_id': rec.user_id.id
                })

    def _onchange_partner_id_values(self, partner_id):
        res = super(CrmLead, self)._onchange_partner_id_values(partner_id)
        if res:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.state_id:
                res.update({
                    'commercial_zone_id':
                        partner.state_id.commercial_zone_id.id
                })

            # Delete every prevision
            res.update({
                'customer_prevision_ids': [(5,)]
            })
        return res
