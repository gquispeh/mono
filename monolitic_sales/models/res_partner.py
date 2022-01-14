from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


CUSTOMER_SERVICE_FIELDS = [
    'street',
    'zip',
    'city',
    'state_id'
    'user_id',
    'prohibited_partial_shippings',
    'segmentation_ids',
    'vat',
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone')
    inform_on_client_platform = fields.Boolean(
        string='Inform On Client Platform',
    )
    sales_prevision_total = fields.Monetary(
        compute='compute_sales_prevision_count', string="Task Count")
    street = fields.Char(required=True)
    zip = fields.Char(required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one(required=True)
    automatic_billing = fields.Selection(
        string='Automatic billing',
        selection=[
            ('none', 'None'),
            ('daily', 'Daily'),
            ('15 days', '15 days')
        ],
        default="none"
    )

    def compute_sales_prevision_count(self):
        for partner in self:
            all_partners = self.with_context(active_test=False).search([
                ('id', 'child_of', partner.ids)])
            all_partners.read(['parent_id'])

            prevision_obj = self.env['commercial.monthly.amount'].search([
                ('partner_id', 'in', all_partners.ids)])
            partner.sales_prevision_total = sum(prevision_obj.mapped('amount'))

    @api.onchange('state_id')
    def _onchange_state(self):
        res = super()._onchange_state()
        if self.state_id:
            self.commercial_zone_id = self.state_id.commercial_zone_id
        return res

    def action_open_sales_prevision(self):
        action = self.env.ref(
            'monolitic_sales.action_sales_prevision_amount').read()[0]
        action['context'] = {}
        action['domain'] = [('partner_id', 'child_of', self.ids)]
        return action

    # @api.model
    # def create(self, values):
    #     user = self.env.user
    #     odoobot = self.env.ref('base.user_root')
    #     if user != odoobot:
    #         for field in CUSTOMER_SERVICE_FIELDS:
    #             if field in values:
    #                 if (
    #                     not self.env.user.sudo().has_group(
    #                         'monolitic.monolitic_commercial_customer_support')
    #                 ):
    #                     raise ValidationError(_(
    #                         "Only a Customer Service user can "
    #                         "set the field %s!") % field)

    #     res = super(ResPartner, self).create(values)

    #     return res

    # def write(self, vals):
    #     res = super(ResPartner, self).write(vals)

    #     if not self.env.context.get("import_write"):
    #         user = self.env.user
    #         odoobot = self.env.ref('base.user_root')
    #         if user != odoobot:
    #             for rec in self:
    #                 for field in CUSTOMER_SERVICE_FIELDS:
    #                     if field in vals:
    #                         if (
    #                             not self.env.user.sudo().has_group(
    #                                 'monolitic.monolitic_commercial_customer_support')
    #                         ):
    #                             raise ValidationError(_(
    #                                 "Only a Customer Service user can "
    #                                 "edit the field %s!") % field)

    #     return res

    @api.model
    def _commercial_fields(self):
        """ Returns the list of fields that are managed by the commercial entity
        to which a partner belongs. These fields are meant to be hidden on
        partners that aren't `commercial entities` themselves, and will be
        delegated to the parent `commercial entity`. The list is meant to be
        extended by inheriting classes. """

        return [
            'vat', 'credit_limit', 'category_id', 'website', 'is_customer',
            'commercial_zone_id', 'user_id', 'property_delivery_carrier_id',
            'team_id', 'property_payment_term_id', 'customer_payment_mode_id',
            'number_of_invoice_copies', 'supplier_id', 'business_option',
            'inform_on_client_platform', 'is_supplier',
            'property_supplier_payment_term_id', 'supplier_payment_mode_id',
            'receipt_reminder_email', 'property_purchase_currency_id',
            'supplier_classification', 'product_category_id',
            'register_project_protection', 'warranty', 'lead_time',
            'property_account_position_id', 'aeat_anonymous_cash_customer',
            'monolitic_supplier_code', 'industry_id', 'activity_id',
            'segmentation_ids', 'strategic_classification',
            'property_stock_customer', 'property_stock_supplier',
            'not_valued_picking', 'prohibited_partial_shippings',
            'automatic_billing', 'not_in_mod347',
            'reminder_date_before_receipt', 'company_credit_limit',
            'insurance_credit_limit', 'risk_insurance_coverage_percent',
            'risk_insurance_requested', 'risk_insurance_grant_date',
            'risk_insurance_code', 'risk_insurance_code_2', 'credit_policy_state_id',
            'warranty_type', 'lead_time_type', 'recommended_annual_visits',
            'logistic_customer_tag', 'logistic_customer_tag_type'
        ]
