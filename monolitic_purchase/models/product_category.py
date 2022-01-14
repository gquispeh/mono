# Copyright 2020 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    product_manager = fields.Many2many('res.users', 'res_users_product_manager', 'res_users_id', 'product_manager_id', string='PM', required=True)
    
    field_application_engineer = fields.Many2many('res.users', 'res_users_field_application_engineer', 'res_users_id', 'field_application_engineer_id', string='FAE', required=True)

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id.product_manager or \
                self.parent_id.field_application_engineer:
            self.product_manager = self.parent_id.product_manager
            self.field_application_engineer = self.parent_id.\
                field_application_engineer

    def unlink(self):
        for rec in self:
            if rec.product_count or rec.child_id.filtered('product_count'):
                raise UserError(
                    _('You cannot delete this category if there are products'
                      ' associated with it or with its childs')
                )
        return super(ProductCategory, self).unlink()

    # @api.depends('name', 'parent_id.complete_name')
    # def _compute_complete_name(self):
    #     for category in self:
    #         if category.parent_id and category.parent_id.id != 1:
    #             category.complete_name = '%s / %s' % (
    #                 category.parent_id.complete_name, category.name)
    #             print(category.complete_name)
    #         else:
    #             category.complete_name = category.name
    #             print(category.name)
