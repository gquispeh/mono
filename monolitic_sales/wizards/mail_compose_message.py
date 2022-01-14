# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

import logging
_logger = logging.getLogger(__name__)


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, auto_commit=False):
        res = super(MailComposer, self).send_mail()
        for wizard in self:
            mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')
            if wizard.model and not mass_mode:
                if wizard.model == 'sale.order':
                    order_obj = self.env[wizard.model].browse([wizard.res_id])
                    # Send PRO-FORMA
                    if self.env.context.get('proforma'):
                        if order_obj.state == 'sale_to_acuse':
                            order_obj.write({'state': 'pending_payment'})
                            return res

                    # Send ORDER
                    if order_obj.state == 'sale':
                        order_obj.state = 'sale_confirmed'
                    if order_obj.state == 'sale_to_acuse':
                        self.env.context = self.with_context(
                            acuse_sent=True).env.context
                        order_obj.action_confirm()

                    order_obj.confirmation_number += 1

        return res
