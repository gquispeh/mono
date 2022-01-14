from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    max_quantity = fields.Float(string='Maximum quantity')
    customer_id = fields.Many2one(string='Customer')
