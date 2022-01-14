
from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    advanced_payment = fields.Boolean(
        string='Advanced Payment',
    )
