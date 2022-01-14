from odoo import models, api, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

FINANCIAL_RISK_FIELDS = [
    'risk_sale_order_include',
    'risk_invoice_draft_include',
    'risk_invoice_open_include',
    'risk_invoice_unpaid_include',
    'risk_account_amount_include',
    'risk_account_amount_unpaid_include',
    'risk_total',
    'risk_invoice_draft_limit',
    'risk_invoice_open_limit',
    'risk_invoice_unpaid_limit',
    'risk_account_amount_limit',
    'risk_account_amount_unpaid_limit',
    'credit_currency',
    'risk_currency_id',
    'manual_credit_currency_id',
    'credit_limit',
    'credit_policy',
    'risk_exception'
]
ACCOUNTING_FIELDS = [
   'bank_ids',
   'property_account_receivable_id',
   'property_account_payable_id'
]
CREDIT_CONTROL_FIELDS = [
   'credit_policy_id',
   'payment_responsible_id',
   'payment_note',
   'payment_next_action_type',
   'payment_next_action',
   'payment_next_action_date',
]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    recommended_annual_visits = fields.Integer(
        string='Recommended annual visits')
    number_of_invoice_copies = fields.Integer(
        string='Number of Invoice Copies')

    partner_activity_ids = fields.Many2many(
        comodel_name='res.partner.activity',
        compute='_compute_partner_activity_ids',
    )
    activity_id = fields.Many2many(
        string='Activity',
        comodel_name='res.partner.activity',
    )
    include_on_mailing = fields.Many2many(
        string='Include on mailing',
        comodel_name='contact.mail.options',
        relation="res_partner_mail_options_include_rel",
        column1="include_partner_id",
        column2="include_contact_mail_options_id",
    )
    exclude_on_mailing = fields.Many2many(
        string='Exclude on mailing',
        comodel_name='contact.mail.options',
        relation="res_partner_mail_options_exclude_rel",
        column1="exclude_partner_id",
        column2="exclude_contact_mail_options_id",
    )
    function = fields.Many2many(
        string='Function',
        comodel_name='res.partner.job',
    )
    credit_policy = fields.Many2one(
        comodel_name='credit.policy',
    )
    extra_limit = fields.Char(
        string='Extra Limit',
    )

    def name_get(self):
        result = []
        origin = super(ResPartner, self).name_get()
        orig_name = dict(origin)
        for rec in self:
            name = ""
            value = orig_name[rec.id]
            if rec.ref:
                name = rec.ref + ' - '
            name += value
            if rec.parent_id and rec.name != rec.parent_id.name:
                name = name.replace(rec.name, '(' + rec.name + ')')
            result.append((rec.id, name))
        return result

    @api.depends('is_customer', 'is_supplier')
    def _compute_partner_activity_ids(self):
        domain = [('partner_type', '=', False)]
        for rec in self:
            if rec.is_customer and rec.is_supplier:
                domain = []
            elif rec.is_customer:
                domain = [
                    '|',
                    ('partner_type', '=', 'customer'),
                    ('partner_type', '=', False),
                ]
            elif rec.is_supplier:
                domain = [
                    '|',
                    ('partner_type', '=', 'supplier'),
                    ('partner_type', '=', False),
                ]

            partner_activity_obj = self.env[
                'res.partner.activity'].search(domain)
            rec.partner_activity_ids = partner_activity_obj.ids

    def replicate_user_ids_contact(self):
        for rec in self:
            _logger.info('CHANGING PARTNER %s', rec.ref)
            if rec.user_id:
                contacts = self.env['res.partner'].search([(
                    'parent_id', '=', rec.id)])
                if contacts:
                    contacts.write({
                        'user_id': [(6, 0, rec.user_id.ids)]
                    })

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        return super(ResPartner, self.with_context(
            mail_post_autofollow=True)).message_post(**kwargs)

    @api.model
    def create(self, values):
        if (
            values.get('company_type') == 'company' and
            not self.env.user.has_group('monolitic_base.group_create_company')
        ):
            raise UserError(_(
                    "Only a Company create user can "
                    "create a company partner."))

        for field in CREDIT_CONTROL_FIELDS:
            if field in values:
                if values[field] != False or values.get('credit_control_analysis_ids') != False:
                    if (
                        not self.env.user.sudo().has_group(
                            'monolitic_base.group_credit_control')
                    ):
                        raise UserError(_(
                            "Only a Control Credit user can "
                            "set the field %s!") % field)

        if values.get('bank_ids') != []:
            if (
                not self.env.user.sudo().has_group(
                    'monolitic_base.group_accounting')
            ):
                raise UserError(_(
                    "Only a Accounting user can "
                    "set the field %s!") % field)

        return super(ResPartner, self).create(values)

    def write(self, vals):
        for rec in self:
            if (
                rec.company_type == 'company' and
                not self.env.user.has_group('monolitic_base.group_create_company')
            ):
                raise UserError(_(
                        "Only a Company create user can "
                        "write a company partner."))

            # for field in FINANCIAL_RISK_FIELDS:
            #     if field in vals:
            #         if (
            #             not self.env.user.sudo().has_group(
            #                 'monolitic_base.group_financial_risk')
            #         ):
            #             raise UserError(_(
            #                 "Only a Financial Risk user can "
            #                 "set the field %s!") % field)

            # for field in CREDIT_CONTROL_FIELDS:
            #     if field in vals:
            #         if (
            #             not self.env.user.sudo().has_group(
            #                 'monolitic_base.group_credit_control')
            #         ):
            #             raise UserError(_(
            #                 "Only a Control Credit user can "
            #                 "set the field %s!") % field)

            # for field in ACCOUNTING_FIELDS:
            #     if field in vals:
            #         if (
            #             not self.env.user.sudo().has_group(
            #                 'monolitic_base.group_accounting')
            #         ):
            #             raise UserError(_(
            #                 "Only a Accounting user can "
            #                 "set the field %s!") % field)

        return super(ResPartner, self).write(vals)

    def unlink(self):
        for rec in self:
            if (
                rec.company_type == 'company' and
                not self.env.user.has_group('monolitic_base.group_create_company')
            ):
                raise UserError(_(
                    "Only a Company create user can "
                    "unlink a company partner."))

        return super(ResPartner, self).unlink()
