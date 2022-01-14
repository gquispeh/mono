# Copyright 2021 Jordi Jane <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pricelist_name = fields.Char(string='Pricelist Name', readonly=True)
    pricelist_price = fields.Float(
        string='Pricelist Price',
        digits='Product Price',
    )
    pricelist_date_start = fields.Datetime('Start Date', readonly=True)
    pricelist_date_end = fields.Datetime('End Date', readonly=True)

    requested_shipping_date = fields.Datetime(
        string='Requested shipping date',
        default=fields.Datetime.now(),
    )
    estimated_shipping_date = fields.Datetime(
        string='Estimated shipping date',
    )
    date_order = fields.Datetime(
        string='Date Order',
        related="order_id.date_order"
    )
    client_order_ref = fields.Char(
        string='Customer Order',
        related="order_id.client_order_ref"
    )
    clasif_customer = fields.Char(
        string='Clasif Customer',
        compute='_compute_clasif_customer',
        size=1,
        store=True
    )
    user_id = fields.Many2one(
        string='Commercial',
        related="order_id.user_id"
    )
    invoice_paid = fields.Boolean(
        string='Paid',
        compute='_compute_paid',
    )
    client_segmentation_id = fields.Many2one(
        string='Market Segmentation',
        comodel_name='monolitic.client.segmentation',
    )
    delivery_term = fields.Char(string='Delivery term')
    max_quantity = fields.Float(
        string='Maximum quantity',
        digits='Product Unit of Measure',
    )
    quantity_report = fields.Char(compute="_compute_quantity_report")
    confirm_line = fields.Boolean(default=True)
    approve_price = fields.Boolean(default=False)
    can_edit_pricelist_price = fields.Boolean(
        compute="_compute_can_edit_pricelist_price")
    pricelist_discount = fields.Float(
        string='Disc. (%)', digits='Discount', default=0.0)

    def _compute_can_edit_pricelist_price(self):
        self.can_edit_pricelist_price = False
        if self.env.user.has_group(
            "monolitic_sales.edit_pricelist_price"
        ):
            self.can_edit_pricelist_price = True

    def action_sale_order_form(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders')
        form = self.env.ref('sale.view_order_form')
        action = action.read()[0]
        action['views'] = [(form.id, 'form')]
        action['res_id'] = self.order_id.id
        return action

    def _compute_quantity_report(self):
        for rec in self:
            rec.quantity_report = str(int(
                rec.product_qty)) + ' - ' + str(int(rec.max_quantity))

    @api.depends('customer_lead', 'order_id.date_order')
    def _compute_estimated_shipping_date(self):
        for record in self:
            record.estimated_shipping_date = record.order_id.expected_date

    @api.onchange('customer_lead', 'requested_shipping_date')
    def _onchange_requested_shipping_date(self):
        for line in self:
            requested_shipping_date = (
                line.requested_shipping_date
                if line.requested_shipping_date else fields.Datetime.now()
            )
            if line.state != 'cancel' and not line._is_delivery():
                line.estimated_shipping_date = requested_shipping_date + \
                    timedelta(days=line.customer_lead or 0.0)

    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def _onchange_price_quantity(self):
        if self.order_id.pricelist_id:

            self.pricelist_name = self.order_id.pricelist_id.name
            self.pricelist_price = self.env[
                'account.tax']._fix_tax_included_price_company(
                    self._get_display_price(self.product_id),
                    self.product_id.taxes_id, self.tax_id, self.company_id)
            categ_ids = {}
            categ = self.product_template_id.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
            categ_ids = list(categ_ids)

            # Get pricelist max quantity for sale order
            pricelists_domain = [
                ('pricelist_id', '=', self.order_id.pricelist_id.id),
                '|', '|',
                ('product_tmpl_id', '=', self.product_template_id.id),
                ('product_id', 'in', self.product_template_id.product_variant_ids.ids),
                ('categ_id', 'in', categ_ids),
            ]
            pricelist_items = self.env[
                'product.pricelist.item'].search(pricelists_domain)

            # Search pricelist
            self.max_quantity = 0
            self.pricelist_date_start = False
            self.pricelist_date_end = False

            qty = self.product_uom_qty
            for pricelist in pricelist_items:
                min_quantity = 0
                if pricelist.min_quantity:
                    min_quantity = pricelist.min_quantity
                # If no value is set on max qty, set it to "Infinite"
                max_quantity = 999999999999
                if pricelist.max_quantity:
                    max_quantity = pricelist.max_quantity
                if qty < min_quantity or qty > max_quantity:
                    continue
                self.max_quantity = pricelist.max_quantity
                self.pricelist_date_start = pricelist.date_start
                self.pricelist_date_end = pricelist.date_end

    def get_downpayment_total_amount(self):
        for line in self:
            amount = 0.0
            if line.is_downpayment:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(
                    price,
                    line.order_id.currency_id,
                    1,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id)
                amount = taxes['total_included']
        return amount

    @api.depends('order_partner_id.strategic_classification')
    def _compute_clasif_customer(self):
        for record in self:
            customer = record.order_partner_id.strategic_classification.name
            record.clasif_customer = customer

    @api.depends('invoice_lines.move_id.state')
    def _compute_paid(self):
        for record in self:
            if record.invoice_lines:
                if record.invoice_lines[0].move_id.state == 'paid':
                    record.invoice_paid = True
                else:
                    record.invoice_paid = False
            else:
                record.invoice_paid = False

    '''
        Inherit function to set as to invoice when on
        'sale_confirmed', 'pending_payment' state
    '''
    @api.depends('state', 'price_reduce', 'product_id', 'untaxed_amount_invoiced', 'qty_delivered', 'product_uom_qty')
    def _compute_untaxed_amount_to_invoice(self):
        """ Total of remaining amount to invoice on the sale order line (taxes excl.) as
                total_sol - amount already invoiced
            where Total_sol depends on the invoice policy of the product.

            Note: Draft invoice are ignored on purpose, the 'to invoice' amount should
            come only from the SO lines.
        """
        for line in self:
            amount_to_invoice = 0.0
            if line.state in ['sale_confirmed', 'done', 'pending_payment']:
                # Note: do not use price_subtotal field as it returns zero when the ordered quantity is
                # zero. It causes problem for expense line (e.i.: ordered qty = 0, deli qty = 4,
                # price_unit = 20 ; subtotal is zero), but when you can invoice the line, you see an
                # amount and not zero. Since we compute untaxed amount, we can use directly the price
                # reduce (to include discount) without using `compute_all()` method on taxes.
                price_subtotal = 0.0
                if line.state == 'pending_payment':
                    uom_qty_to_consider = line.product_uom_qty
                else:
                    uom_qty_to_consider = line.qty_delivered if line.product_id.invoice_policy == 'delivery' else line.product_uom_qty
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                price_subtotal = price_reduce * uom_qty_to_consider
                if len(line.tax_id.filtered(lambda tax: tax.price_include)) > 0:
                    # As included taxes are not excluded from the computed subtotal, `compute_all()` method
                    # has to be called to retrieve the subtotal without them.
                    # `price_reduce_taxexcl` cannot be used as it is computed from `price_subtotal` field. (see upper Note)
                    price_subtotal = line.tax_id.compute_all(
                        price_reduce,
                        currency=line.order_id.currency_id,
                        quantity=uom_qty_to_consider,
                        product=line.product_id,
                        partner=line.order_id.partner_shipping_id)['total_excluded']

                if any(line.invoice_lines.mapped(lambda l: l.discount != line.discount)):
                    # In case of re-invoicing with different discount we try to calculate manually the
                    # remaining amount to invoice
                    amount = 0
                    for l in line.invoice_lines:
                        if len(l.tax_ids.filtered(lambda tax: tax.price_include)) > 0:
                            amount += l.tax_ids.compute_all(l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity)['total_excluded']
                        else:
                            amount += l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity

                    amount_to_invoice = max(price_subtotal - amount, 0)
                else:
                    amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced

            line.untaxed_amount_to_invoice = amount_to_invoice

    '''
        Inherit function to set as to invoice when on
        'sale_confirmed', 'pending_payment' state
    '''
    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('sale_confirmed', 'done', 'pending_payment'):
                line.invoice_status = 'no'
            elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
                line.invoice_status = 'invoiced'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    '''
        Inherit function to set as to invoice when on
        'sale_confirmed', 'pending_payment' state
    '''
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale_confirmed', 'done', 'pending_payment']:
                if line.product_id.invoice_policy == 'order' or line.order_id.state == 'pending_payment':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    def _prepare_invoice_line(self, **optional_values):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        vals.update({
            'client_segmentation_id': self.client_segmentation_id.id,
            'pricelist_name': self.pricelist_name,
            'pricelist_price': self.pricelist_price,
            'pricelist_date_start': self.pricelist_date_start,
            'pricelist_date_end': self.pricelist_date_end,
            'product_segmentation_id': self.product_id.categ_id.id,
            'date': self.date_order,
            'user_id': self.user_id.id
        })
        return vals

    @api.onchange('commitment_date')
    def _onchange_commitment_date(self):
        if (
            self.state in ['sale', 'sale_confirmed'] and
            self.product_id.type in ['product', 'consu'] and
            self.commitment_date
        ):
            move = self.env['stock.move'].search([
                ('sale_line_id', '=', self._origin.id),
                ('state', 'not in', ['assigned', 'done']),
            ])
            if move:
                move.date = self.commitment_date
                move.date_deadline = self.commitment_date

    # Override to update qty on stock moves
    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # When modifying a one2many, _origin doesn't guarantee
        # that its values will be the ones
        # in database. Hence, we need to explicitly read them from there.
        if self._origin:
            product_uom_qty_origin = self._origin.read(
                ["product_uom_qty"])[0]["product_uom_qty"]
        else:
            product_uom_qty_origin = 0

        if (
            self.state in ['sale', 'sale_confirmed'] and
            self.product_id.type in ['product', 'consu'] and
            self.product_uom_qty != product_uom_qty_origin
        ):
            move = self.env['stock.move'].search([
                ('sale_line_id', '=', self._origin.id),
                ('state', 'not in', ['assigned', 'done']),
            ])
            if move:
                if (
                    move.quantity_done > self.product_uom_qty or
                    move.reserved_availability > self.product_uom_qty
                ):
                    raise ValidationError(_(
                        "Quantity requested cannot be less than "
                        "quantity already reserved/delivered!"))
                else:
                    move.product_uom_qty = self.product_uom_qty
            else:
                raise ValidationError(_(
                    "Couldn't update quantity on stock move due to "
                    "stock move not found or already reserved/done!"))
        return {}

    @api.onchange('pricelist_discount')
    def _onchange_pricelist_discount(self):
        if not self.env.context.get("skip_onchange"):
            if (
                not self.env.user.has_group('monolitic_sales.group_discount_sale_lines') and
                self.pricelist_discount > 10
            ):
                raise ValidationError(_(
                    "You can't add a discount superior to 10% !"))

            if self.price_unit:
                self.price_unit = self.pricelist_price - (
                    self.pricelist_price * (self.pricelist_discount / 100))
                # Do not force another onchange, infinite loop
                self.env.context = self.with_context(skip_onchange=True).env.context

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        if not self.env.context.get("skip_onchange"):
            if self.pricelist_price:
                self.pricelist_discount = (
                    (self.pricelist_price - self.price_unit) * 100 / self.pricelist_price)
                # Do not force another onchange, infinite loop
                self.env.context = self.with_context(skip_onchange=True).env.context
