# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments = super()._create_payments()

        context = self.env.context
        if 'active_ids' in context:
            for active_id in context['active_ids']:
                invoice = self.env['account.move'].browse([active_id])
                orders = set()
                for line in invoice.invoice_line_ids:
                    for sale_line in line.sale_line_ids:
                        orders.add(sale_line.order_id)
                    for order in orders:
                        if order.state == 'pending_payment':
                            order.state = 'sale_to_acuse'

        return payments
