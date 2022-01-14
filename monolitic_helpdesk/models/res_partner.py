
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tickets_count = fields.Integer("Tasks")
