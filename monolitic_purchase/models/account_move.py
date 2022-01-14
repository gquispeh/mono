# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _get_default_invoice_date(self):
        return (
            fields.Date.context_today(self) if
            self._context.get('default_move_type', 'entry') in
            self.get_purchase_types(include_receipts=True) else False
        )

    invoice_date = fields.Date(
        default=_get_default_invoice_date,
    )

    @api.constrains('invoice_date', 'date')
    def _supplier_invoice_date_constrains(self):
        for rec in self:
            if rec.move_type in self.get_purchase_types(include_receipts=True):
                if date.today() < rec.invoice_date:
                    raise ValidationError(_(
                        "Invoice date can't be superior than today!"))
                if rec.date < rec.invoice_date:
                    raise ValidationError(_(
                        "Accounting date can't be inferior than invoice date!"))
