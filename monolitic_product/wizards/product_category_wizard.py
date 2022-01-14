# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductCategoryWizard(models.TransientModel):
    _name = 'product.category.wizard'
    _inherit = 'category.levels.mixing'
    _description = 'Product Category Wizard'

    level_1 = fields.Many2one(string="Área de negocio")
    level_2 = fields.Many2one(string="Línea de negocio")
    level_3 = fields.Many2one(string="Gama de producto")
    level_4 = fields.Many2one(string="Línea de producto")
    level_5 = fields.Many2one(string="Sublínea de producto")

    '''
    def get_allow_categ_ids_product(self, obj_id):
        allow_categ = []
        sellers_categories = obj_id.seller_ids.mapped('name').\
            mapped('product_category_id')
        for categ in sellers_categories:
            allow_categ.append(categ.id)
            parent_id = categ.parent_id
            while parent_id:
                allow_categ.append(parent_id.id)
                parent_id = parent_id.parent_id
        return self.env['product.category'].\
            browse(allow_categ).filtered(lambda x: x.id != 1)

    def get_allow_categ_ids_activity(self, obj_id):
        allow_categ = []
        if obj_id.product_id:
            sellers_categories = obj_id.product_id.mapped('categ_id')
        elif obj_id.represented_id:
            sellers_categories = obj_id.represented_id[0].mapped(
                'product_category_id')
        else:
            sellers_categories = []
        for categ in sellers_categories:
            allow_categ.append(categ.id)
            parent_id = categ.parent_id
            while parent_id:
                allow_categ.append(parent_id.id)
                parent_id = parent_id.parent_id
        return self.env['product.category'].\
            browse(allow_categ).filtered(lambda x: x.id != 1)
    def get_allow_categ_ids_crm(self, obj_id):
        allow_categ = []
        product_categories = obj_id.lead_id.lead_line_ids.mapped('category_id')
        for categ in product_categories:
            allow_categ.append(categ.id)
            parent_id = categ.parent_id
            while parent_id:
                allow_categ.append(parent_id.id)
                parent_id = parent_id.parent_id
        return self.env['product.category'].\
            browse(allow_categ).filtered(lambda x: x.id != 1)
    '''

    def _compute_allow_categ_ids(self):
        model, res_id = self.get_model_and_id()
        obj_id = self.env[model].browse(res_id)
        if not obj_id:
            raise UserError(
                _("There is not a product select,"
                    " please click on Edit button again"))

        cat_obj = self.env['product.category']

        # if model in ['product.template', 'product.product']:
        #     self.allow_categ_ids = self.get_allow_categ_ids_product(obj_id)
        # elif model in ['mail.activity']:
        #     self.allow_categ_ids = self.get_allow_categ_ids_activity(obj_id)
        # if model in ['customer.prevision']:
        #     self.allow_categ_ids = self.get_allow_categ_ids_crm(obj_id)
        # else:
        self.allow_categ_ids = cat_obj.search([
            ('parent_id', '=', False), ('id', '!=', 1)
        ])

    @api.onchange('allow_categ_ids')
    def _onchange_allow_categ_ids(self):
        domain = [('parent_id', '=', False), ('id', '!=', 1)]
        if not self.allow_categ_ids:
            model, res_id = self.get_model_and_id()
            # obj_id = self.env[model].browse(res_id)
            # if model in ['product.template', 'product.product']:
            #     self.allow_categ_ids = self.get_allow_categ_ids_product
            # (obj_id)
            # elif model in ['mail.activity']:
            #     self.allow_categ_ids = self.get_allow_categ_ids_activity(
            #         obj_id)
            # if model in ['customer.prevision']:
            #     self.allow_categ_ids = self.get_allow_categ_ids_crm(obj_id)
        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: not x.parent_id and x.id != 1
            )
            if len(allow_categ) == 1:
                self.level_1 = allow_categ
                return {}
            domain += [('id', 'in', self.allow_categ_ids.ids)]
        return {'domain': {'level_1': domain}}
