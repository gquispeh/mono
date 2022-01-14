
from odoo import fields, models


class CreditPolicy(models.Model):
    _name = 'credit.policy'

    name = fields.Char()
