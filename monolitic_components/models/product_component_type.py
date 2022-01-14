from odoo import fields, models


class ComponentType(models.Model):
    _name = 'product.component.type'
    _description = 'Component Type'

    name = fields.Char(tracking=True, required=True)
    attributes_ids = fields.Many2many(
        comodel_name='product.attribute',
        string='Attributes')
