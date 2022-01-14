from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    level_parents = fields.Integer(
        string="Category Level",
        compute='_compute_level_parents', search='_search_level_parents',
        store=True)
    property_cost_method = fields.Selection(default='average')

    @api.depends('parent_id')
    def _compute_level_parents(self):
        for rec in self:
            count = 1
            parent_id = rec.parent_id
            while parent_id:
                count += 1
                parent_id = parent_id.parent_id
            rec.level_parents = count

    @api.model
    def _search_level_parents(self, operand, value):
        if operand == '=':
            def f(x): return x.level_parents == value
        elif operand == '>=':
            def f(x): return x.level_parents >= value
        elif operand == '<=':
            def f(x): return x.level_parents <= value
        elif operand == '<':
            def f(x): return x.level_parents < value
        elif operand == '>':
            def f(x): return x.level_parents > value
        else:
            def f(x): return x.level_parents != value
        ids = self.env['product.category'].search([]).filtered(f).ids
        return [('id', 'in', ids)]

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('get_only_name', False):
                # Only goes off when the custom_search
                # is in the context values.
                result.append((record.id, record.name))
            else:
                result.append((record.id, record.complete_name))

        return result
