# Copyright 2020 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from re import template
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from datetime import date
from functools import partial

import calendar
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang, get_lang
from odoo.tools import float_compare

import logging
_logger = logging.getLogger(__name__)

CUSTOMER_SERVICE_FIELDS = [
    'partner_id',
    'user_id',
    'client_order_ref',
    'opportunity_id',
    'prohibited_partial_shippings',
    'partner_shipping_id',
    'partner_invoice_id',
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone')

    offer_type = fields.Selection(string='Offer Type', selection=[
                                  ('est', 'Estimated'), ('buy', 'Buy')])

    user_id = fields.Many2one(domain="[('is_commercial', '=', True)]")

    client_order_ref = fields.Char(string="Customer order")

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale_to_acuse', 'Order to Acuse'),
        ('pending_payment', 'Pending Payment'),
        ('sale', 'Order to Confirm'),
        ('sale_confirmed', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    inform_on_client_platform = fields.Boolean(
        string='Inform On Client Platform',
    )
    generate_due_dates = fields.Boolean(
        compute='_compute_generate_due_dates'
    )
    paid_invoice = fields.Boolean(
        compute='_compute_paid_invoice'
    )
    chance_of_success = fields.Float(string='Chance of Success')

    user_id = fields.Many2one(
        required=True,
    )

    validity_date = fields.Date(
        default=fields.Date.today() + relativedelta(days=30),
    )

    automatic_billing = fields.Selection(
        string='Automatic billing',
        related='partner_id.automatic_billing'
    )
    quotation_id = fields.Many2one(
        string='Quotation',
        comodel_name='sale.order',
    )
    partner_id = fields.Many2one(
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
            'sale_to_acuse': [('readonly', False)]}
    )
    partner_invoice_id = fields.Many2one(
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
            'sale_to_acuse': [('readonly', False)]}
    )
    partner_shipping_id = fields.Many2one(
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
            'sale_to_acuse': [('readonly', False)]},
            check_company=False
    )
    partner_pricelist = fields.Char(compute="_compute_partner_pricelist")
    pricelist_id = fields.Many2one(
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
            'sale_to_acuse': [('readonly', False)]}
    )
    vinculated_sales_orders_count = fields.Integer(
        string='vinculated_sales_orders_count',
        compute="_compute_vinculated_sales_order_count"
    )
    client_seg_ids = fields.Many2many(
        compute='_compute_client_seg_ids',
        comodel_name='monolitic.client.segmentation'
    )
    percent_proforma_payment = fields.Integer('% Payment Proforma')

    remaining_validity_days = fields.Integer(
        string='Remaining Validity Days',
        compute="_compute_remaining_validity_days",
        readonly=True,)
    partner_bank_account_id = fields.Many2one(
        string='Partner Bank Account',
        comodel_name='res.partner.bank',
    )
    delivery_conditions_id = fields.Many2one(
        string='Delivery carrier',
        comodel_name='stock.delivery.condition',
    )
    confirmation_number = fields.Integer(
        string='Confirmation Number', readonly=True,
    )
    partner_parent_id = fields.Many2one(
        string='partner_parent',
        comodel_name='res.partner',
        compute="_compute_partner_parent_id",
        store=True
    )
    has_sale_order = fields.Boolean(compute="_compute_has_sale_order", store=True)

    def _compute_has_sale_order(self):
        for rec in self:
            rec.has_sale_order = False
            if rec.vinculated_sales_orders_count > 0:
                sale_order_ids = rec.env['sale.order'].search([
                    ('quotation_id.id', '=', rec.id)])
                for sale_order in sale_order_ids:
                    if sale_order.state != 'cancel':
                        rec.has_sale_order = True

    @api.onchange('partner_id')
    def _compute_partner_parent_id(self):
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.parent_id:
                    rec.partner_parent_id = rec.partner_id.parent_id
                else:
                    rec.partner_parent_id = rec.partner_id
            else:
                rec.partner_parent_id = False

    @api.depends('validity_date', 'date_order')
    def _compute_remaining_validity_days(self):
        for rec in self:
            aux = rec.validity_date - rec.date_order.date()
            rec.remaining_validity_days = aux.days

    @api.onchange('partner_id')
    def _compute_partner_pricelist(self):
        for rec in self:
            rec.partner_pricelist = \
                rec.partner_id.property_product_pricelist.id

    @api.onchange('partner_id')
    def _compute_client_seg_ids(self):
        domain = []
        for rec in self:
            if rec.partner_id.segmentation_ids:
                domain = [(
                    'id', 'in', self.partner_id.segmentation_ids.ids)]
            segmentations_obj = self.env[
                'monolitic.client.segmentation'].search(domain)
            rec.client_seg_ids = segmentations_obj.ids

    def _compute_vinculated_sales_order_count(self):
        for record in self:
            record.vinculated_sales_orders_count = self.env[
                'sale.order'].search_count([
                    ('quotation_id.id', '=', record.id)
                ])

    def _compute_generate_due_dates(self):
        for rec in self:
            generate_due_dates = True
            if rec.payment_term_id:
                if rec.payment_term_id.advanced_payment:
                    generate_due_dates = False

            rec.generate_due_dates = generate_due_dates

    def _compute_paid_invoice(self):
        for rec in self:
            paid_invoices = rec.invoice_ids.filtered(
                lambda x: x.move_type == 'out_invoice' and
                x.payment_state in ['paid', 'partial', 'in_payment'])
            rec.paid_invoice = True if paid_invoices else False

    @api.onchange('date_order')
    def onchange_date_order(self):
        self.validity_date = self.date_order + relativedelta(days=30)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.partner_id:
            self.inform_on_client_platform \
                = self.partner_id.inform_on_client_platform

            if not self.partner_id.customer_payment_mode_id or \
                    not self.partner_id.vat or \
                    not self.partner_id.property_payment_term_id:
                raise ValidationError(
                    _("This partner doesn't have VAT, Payment mode and Payment\
                        terms. Please fill them up"))
            elif self.payment_mode_id:
                self.payment_mode_id = self.partner_id.customer_payment_mode_id

            # If there are more than one delivery address or invoice address,
            # The field must prevail empty, not to change automatically
            if self.partner_id.child_ids:
                num_delivery_address = 0
                num_invoice_address = 0
                for child in self.partner_id.child_ids:
                    if child.type == 'delivery':
                        num_delivery_address += 1
                    if child.type == 'invoice':
                        num_invoice_address += 1
                if num_delivery_address > 1:
                    self.update({'partner_shipping_id': False})
                if num_invoice_address > 1:
                    self.update({'partner_invoice_id': False})

            if self.partner_id.state_id:
                self.commercial_zone_id = \
                    self.partner_id.state_id.commercial_zone_id

            if self.partner_id.parent_id:
                if self.partner_id.parent_id.property_product_pricelist:
                    self.update({
                        'pricelist_id':
                            self.partner_id.parent_id.property_product_pricelist.id
                    })

            if self.partner_id.parent_id:
                if self.partner_id.parent_id.delivery_conditions_id:
                    self.delivery_conditions_id = \
                        self.partner_id.parent_id.delivery_conditions_id
                else:
                    self.delivery_conditions_id = False
            else:
                if self.partner_id.delivery_conditions_id:
                    self.delivery_conditions_id = \
                        self.partner_id.delivery_conditions_id
                else:
                    self.delivery_conditions_id = False

            if self.partner_id.parent_id:
                if self.partner_id.parent_id.bank_ids:
                    self.partner_bank_account_id = \
                        self.partner_id.parent_id.bank_ids[0]
                else:
                    self.partner_bank_account_id = False
            else:
                if self.partner_id.bank_ids:
                    self.partner_bank_account_id = self.partner_id.bank_ids[0]
                else:
                    self.partner_bank_account_id = False

        return res

    def action_to_acuse(self):
        for rec in self:
            customer_service_group = self.env.ref(
                'monolitic.monolitic_customer_support').sudo()
            for user in customer_service_group.users:
                rec.message_subscribe([user.partner_id.id])

            if rec.generate_due_dates:
                rec.state = 'sale_to_acuse'
            else:
                rec.state = 'pending_payment'

    def action_generate_sale_order(self):
        for line in self.order_line:
            if line.product_id and line.product_id.type == 'product':
                if not line.pricelist_price:
                    raise UserError(_(
                            "Product: %s has no sale pricelist."
                        ) % line.product_id.name)

        if self.partner_id.parent_id:
            if (
                self.partner_id.parent_id.risk_invoice_unpaid +
                self.partner_id.parent_id.risk_account_amount_unpaid
            ) > 0:
                raise UserError(_(
                    'The parent client has an unpaid financial '
                    'risk greater than 0'
                ))
        else:
            if (
                self.partner_id.risk_invoice_unpaid +
                self.partner_id.risk_account_amount_unpaid
            ) > 0:
                raise UserError(_(
                    'The client has an unpaid financial risk greater than 0'
                ))

        # Delete offer validate activity
        # We need to search the summary in es_ES due to translation
        offer_activity = self.env['mail.activity'].search([
            ('summary', 'ilike', 'Oferta a expirar'),
            ('res_model_id', '=', self.env['ir.model']._get(self._name).id),
            ('res_id', '=', self.id),
        ])
        if offer_activity:
            offer_activity.unlink()

        copy = self.copy({
            'quotation_id': self.id,
            'origin': self.name,
            'state': 'sale_to_acuse',
        })
        copy.action_to_acuse()
        copy.write({
            'name': self.env.ref(
                "sale.seq_sale_order", raise_if_not_found=False).next_by_id()
        })

        return {
            'name': copy.name,
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'res_id': copy.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    def action_vinculated_quotations(self):
        sale_order_ids = self.env['sale.order'].search([
            ('quotation_id.id', '=', self.id),
        ]).ids

        return {
            'name': _('Sales Orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'res_id': self.env.context.get('target_id'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('id', 'in', sale_order_ids)]
        }

    def action_confirm(self):
        for rec in self:
            if rec.generate_due_dates and \
                    not self.env.context.get("acuse_sent"):
                raise ValidationError(_(
                    'This order generates due dates, '
                    'sending the acuse is required before proceeding !'))

            if rec.state == 'pending_payment' and not rec.paid_invoice:
                raise ValidationError(_(
                    "This order can't be confirmed manually since the "
                    "invoice has not been paid !"))

            customer_service_group = self.env.ref(
                'monolitic.monolitic_customer_support').sudo()
            for user in customer_service_group.users:
                rec.message_unsubscribe([user.partner_id.id])
        return super().action_confirm()

    def action_back_to_confirm(self):
        for rec in self:
            rec.write({'state': 'sale'})

    def generate_validity_date_activity(self):
        activity_type_id = self.env.ref(
            'mail.mail_activity_data_todo').sudo().id
        activity_values = {
            'activity_type_id': activity_type_id,
            'user_id': self.user_id.id,
            'summary': _("Offer about to expire"),
            'date_deadline': self.validity_date - relativedelta(days=7),
            'res_model_id': self.env['ir.model']._get(self._name).id,
            'res_id': self.id,
        }
        self.env['mail.activity'].sudo().create(activity_values)

    def generate_price_unit_activity(self):
        for rec in self:
            if rec.order_line:
                sales_manager_id = False
                sales_manager_group = self.env.ref(
                    'monolitic.monolitic_sales_director').sudo()
                sale_manager_role = self.env['res.users.role'].sudo().search([(
                    'group_id', '=', sales_manager_group.id)])
                if sale_manager_role.line_ids:
                    sales_manager_id = sale_manager_role.line_ids[0].user_id

                for line in rec.order_line:
                    if not line.approve_price:
                        if line.discount > 10.0:
                            line.confirm_line = False

                            activity_type_id = self.env.ref(
                                'mail.mail_activity_data_todo').sudo().id
                            activity_values = {
                                'activity_type_id': activity_type_id,
                                'user_id': sales_manager_id.id,
                                'summary': _(
                                    "The discount of the product "
                                    + line.product_id.name +
                                    " was set over 10%"
                                ),
                                'note': _(
                                    "The discount of the product "
                                    + line.product_id.name +
                                    " was set over 10%! "
                                ),
                                'res_model_id': self.env['ir.model']._get(
                                    rec._name).id,
                                'res_id': rec.id,
                            }
                            self.env['mail.activity'].create(activity_values)
                        else:
                            line.confirm_line = True

    def action_quotation_send(self):
        for line in self.order_line:
            if line.product_id and line.product_id.type == 'product':
                if not line.pricelist_price:
                    raise UserError(_(
                            "Product: %s has no sale pricelist."
                        ) % line.product_id.name)

        return super(SaleOrder, self).action_quotation_send()

    @api.constrains("validity_date")
    def check_validity_date(self):
        for rec in self:
            if rec.validity_date < rec.date_order.date():
                raise UserError(_(
                    "Validity date cannot be before order date!"))

    @api.model
    def create(self, values):
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            if (
                not values['quotation_id']
                and not self.env.user.has_group('monolitic_sales.group_budget_edition')
            ):
                raise UserError(_(
                    "You don't have permision to create a quotation!"))

            if (
                values['quotation_id']
                and not self.env.user.has_group('monolitic_sales.group_sale_order_edition')
            ):
                raise UserError(_(
                    "You don't have permision to create a sale order!"))

        res = super(SaleOrder, self).create(values)

        customer_service_group = self.env.ref(
            'monolitic.monolitic_customer_support').sudo()
        for user in customer_service_group.users:
            res.message_subscribe([user.partner_id.id])

        if res.order_line:
            res.generate_price_unit_activity()

        if res.validity_date and not res.quotation_id and res.state == 'draft':
            res.generate_validity_date_activity()

        return res

    def write(self, vals):
        for field in vals:
            if field != 'invoice_status':
                if not self.env.user.has_group('sales_team.group_sale_manager'):
                    if (
                        self.state in ['draft', 'sent']
                        and not self.env.user.has_group('monolitic_sales.group_budget_edition')
                    ):
                        raise UserError(_(
                            "You don't have permision to edit a quotation!"))

                    if (
                        self.state not in ['draft', 'sent']
                        and not self.env.user.has_group('monolitic_sales.group_sale_order_edition')
                    ):
                        raise UserError(_(
                            "You don't have permision to edit a sale order!"))

        for line in self.order_line:
            if line.product_id and line.product_id.type == 'product':
                if not line.pricelist_price:
                    raise UserError(_(
                            "Product: %s has no sale pricelist."
                        ) % line.product_id.name)

        res = super(SaleOrder, self).write(vals)

        if not self.env.context.get("import_write"):
            for rec in self:
                if 'validity_date' in vals:
                    offer_activity = self.env['mail.activity'].search([
                        ('summary', 'ilike', 'Oferta a expirar'),
                        ('res_model_id', '=', self.env['ir.model']._get(rec._name).id),
                        ('res_id', '=', rec.id),
                    ])
                    offer_activity.write({
                        'date_deadline': rec.validity_date - relativedelta(days=7)
                    })

                if 'order_line' in vals:
                    rec.generate_price_unit_activity()

                if 'payment_term_id' in vals:
                    if (
                        rec.state == 'sale_to_acuse' and
                        not rec.generate_due_dates
                    ):
                        rec.write({'state': 'pending_payment'})
                    elif rec.state == 'pending_payment' and rec.generate_due_dates:
                        rec.write({'state': 'sale_to_acuse'})

        return res

    def update_prices(self):
        super().update_prices()
        lines_to_update = []
        for line in self.order_line.filtered(lambda line: not line.display_type):
            product = line.product_id.with_context(
                partner=self.partner_id,
                quantity=line.product_uom_qty,
                date=self.date_order,
                pricelist=self.pricelist_id.id,
                uom=line.product_uom.id
            )
            pricelist_price = self.env[
                'account.tax']._fix_tax_included_price_company(
                    line._get_display_price(product),
                    line.product_id.taxes_id,
                    line.tax_id, line.company_id)

            lines_to_update.append((
                1, line.id, {'pricelist_price': pricelist_price}))
            self.update({'order_line': lines_to_update})

    def copy(self, default=None):
        context = dict(self._context)
        if (
            not self.generate_due_dates and
            self.state not in ['draft', 'sent', 'cancel']
        ):
            context['default_state'] = 'pending_payment'

        res = super(
            SaleOrder, self.with_context(context)).copy(default=default)

        res.origin = self.name
        if res.state in ['draft', 'sent', 'cancel']:
            # Re-calculate prices
            res.update_prices()
        return res

    @api.onchange('partner_id', 'order_line')
    def onchange_opportunity_id(self):
        for rec in self:
            domain = [('type', '=', 'opportunity')]
            if rec.partner_id:
                domain += [
                    ('partner_id', '=', rec.partner_id.id)
                ]

            # Apparently doesnt exist on v14
            #
            # if rec.order_line:
            #     lead_lines = self.env['crm.lead.line'].search([(
            #         'product_id', 'in', rec.order_line.mapped(
            #             'product_id').ids)])
            #     if lead_lines:
            #         if rec.partner_id:
            #             domain.insert(1, ('|'))
            #         domain += [
            #             ('lead_line_ids', 'in', lead_lines.ids)
            #         ]

            opportunity = self.env['crm.lead'].search(domain)

            return {
                'domain': {
                    'opportunity_id': [('id', 'in', opportunity.ids)]
                }
            }

    '''
        Inherit function to set as to invoice when on
        'sale_confirmed', 'pending_payment' state
    '''
    @api.depends('state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale_confirmed', 'done', 'pending_payment'])

        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d['order_id'][0], d['invoice_status'])
            for d in self.env['sale.order.line'].read_group([
                    ('order_id', 'in', confirmed_orders.ids),
                    ('is_downpayment', '=', False),
                    ('display_type', '=', False),
                ],
                ['order_id', 'invoice_status'],
                ['order_id', 'invoice_status'], lazy=False)]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in ('sale_confirmed', 'done', 'pending_payment'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    def check_sale_orders(self):
        last_day_of_month = calendar.monthrange(
            date.today().year, date.today().month)[1]
        domain = [('automatic_billing', '=', 'daily')]
        if date.today().day == 15 or date.today().day == last_day_of_month:
            domain = [('automatic_billing', 'in', ('daily', '15 days'))]

        for partner in self.env['res.partner'].search(domain):
            orders_to_invoice = partner.sale_order_ids.filtered(
                lambda x: x.invoice_status == 'to invoice')
            if orders_to_invoice:
                inv_wizard_obj = self.env['sale.advance.payment.inv'].create({
                    'advance_payment_method': 'delivered',
                })
                inv_wizard_obj.with_context(
                    active_ids=orders_to_invoice.ids).create_confirm_invoices()

    def get_down_payment_untax_amount(self):
        for rec in self:
            total_untax = 0.0
            for line in rec.order_line:
                if line.is_downpayment:
                    total_untax += line.price_unit
            return total_untax

    def get_down_payment_total_amount(self):
        for rec in self:
            total_amount = 0.0
            for line in rec.order_line:
                if line.is_downpayment:
                    total_amount += line.get_downpayment_total_amount()
            return total_amount

    amount_by_group_downpayment = fields.Binary(
        string="Tax amount by group",
        compute='_amount_by_group_downpayment',
    )

    def _amount_by_group_downpayment(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(
                lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                if line.is_downpayment:
                    price_reduce = (
                        line.price_unit * (1.0 - line.discount / 100.0))
                    taxes = line.tax_id.compute_all(
                        price_reduce,
                        quantity=1,
                        product=line.product_id,
                        partner=order.partner_shipping_id)['taxes']
                    for tax in line.tax_id:
                        group = tax.tax_group_id
                        res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                        for t in taxes:
                            if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                                res[group]['amount'] += t['amount']
                                res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group_downpayment = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]

    # def _create_invoices(self, grouped=False, final=False, date=None):
    #     for rec in self:
    #         if rec.partner_id.parent_id:
    #             if (
    #                 rec.partner_id.parent_id.risk_invoice_unpaid +
    #                 rec.partner_id.parent_id.risk_account_amount_unpaid
    #             ) > 0:
    #                 raise UserError(_(
    #                     'The parent client has an unpaid financial '
    #                     'risk greater than 0'
    #                 ))
    #         else:
    #             if (
    #                 rec.partner_id.risk_invoice_unpaid +
    #                 rec.partner_id.risk_account_amount_unpaid
    #             ) > 0:
    #                 raise UserError(_(
    #                     'The client has an unpaid financial risk greater than 0'
    #                 ))
    #     return super(SaleOrder, self)._create_invoices(grouped, final, date)

    '''
        Override function to get by default Monolitic custom templates
    '''
    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        # Get templates by ID since we don't have XML ID
        if self.env.context.get('proforma', False):
            template_id = 61  # Proforma template
        else:
            if self.state in ['draft', 'sent', 'cancel']:
                template_id = 62  # Quotation template
            elif self.state in ['sale_to_acuse', 'pending_payment']:
                template_id = 60  # Acuse template
            elif self.state in ['sale', 'sale_confirmed', 'done']:
                template_id = 65  # Confirmation template

        return template_id
