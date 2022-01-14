from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone')

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.partner_id:
            if self.partner_id.state_id:
                self.commercial_zone_id = \
                    self.partner_id.state_id.commercial_zone_id
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        return super(AccountMove, self.with_context(
            mail_post_autofollow=True)).message_post(**kwargs)

    # def action_post(self):
    #     if self.partner_id.parent_id:
    #         if (
    #             self.partner_id.parent_id.risk_invoice_unpaid +
    #             self.partner_id.parent_id.risk_account_amount_unpaid
    #         ) > 0:
    #             raise UserError((
    #                 'The parent client has an unpaid financial '
    #                 'risk greater than 0'
    #             ))
    #     else:
    #         if (
    #             self.partner_id.risk_invoice_unpaid +
    #             self.partner_id.risk_account_amount_unpaid
    #         ) > 0:
    #             raise UserError((
    #                 'The client has an unpaid financial risk greater than 0'
    #             ))
    #     return super(AccountMove, self).action_post()

    @api.model
    def create(self, values):
        if 'default_state' in self._context:
            ctx = {
                key: val for key, val in self._context.items()
                if key != 'default_state'
            }
            self = self.with_context(ctx)
        return super(AccountMove, self).create(values)
