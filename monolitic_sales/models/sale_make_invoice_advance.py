from odoo import models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    def create_validate_invoice(self, sale):
        if self.advance_payment_method == 'delivered':
            draft_invoice = sale._create_invoices(
                final=self.deduct_down_paymentss)
            draft_invoice.action_post()

    def create_confirm_invoices(self):
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))
        for sale in sale_orders:
            self.with_delay().create_validate_invoice(sale)
