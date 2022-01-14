# Copyright 2021 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class CategoryLevelsMixing(models.AbstractModel):
    _name = 'category.levels.mixing'
    _description = 'Abstract Model for manage Category Levels'

    def get_model_and_id(self):
        return (self._context.get('active_model',
                                  ''), self._context['active_id'])

    def get_object(self):
        return self.env['product.category']

    init_category_id = fields.Many2one(comodel_name='product.category',
                                       compute="_compute_init_category_id")

    def _compute_init_category_id(self):
        for rec in self:
            rec.init_category_id = False
            if not self._context.get('many2many_field'):
                field = self._context.get('field_to_write', False) \
                    or 'categ_id'
                model, res_id = self.get_model_and_id()
                res_data = self.env[model].search_read(
                    [('id', '=', res_id)], [field])
                if res_data:
                    cat_id = res_data[0].get(field, [[]])
                    if cat_id:
                        rec.init_category_id = self.get_object().browse(
                            cat_id[0])
                    print(rec.init_category_id)

    num_required = fields.Integer()
    level_1 = fields.Many2one("product.category")
    level_2 = fields.Many2one("product.category")
    level_3 = fields.Many2one("product.category")
    level_4 = fields.Many2one("product.category")
    level_5 = fields.Many2one("product.category")

    hide_level_2 = fields.Boolean(default=True)
    hide_level_3 = fields.Boolean(default=True)
    hide_level_4 = fields.Boolean(default=True)
    hide_level_5 = fields.Boolean(default=True)

    allow_categ_ids = fields.Many2many(comodel_name='product.category',
                                       compute="_compute_allow_categ_ids")

    def levels_contraints(self):
        labels = {
            'level_1': self.fields_get('level_1').get('level_1', {}).
            get('string', 'level_1'),
            'level_2': self.fields_get('level_2').get('level_2', {}).
            get('string', 'level_2'),
            'level_3': self.fields_get('level_3').get('level_3', {}).
            get('string', 'level_3'),
            'level_4': self.fields_get('level_4').get('level_4', {}).
            get('string', 'level_4'),
            'level_5': self.fields_get('level_5').get('level_5', {}).
            get('string', 'level_5'),
        }
        if self._context.get('skip_validation'):
            return None
        if not self.level_1 and self.num_required >= 1:
            label = labels.get('level_1', 'level_1')
            raise ValidationError(_("The field %s is required") % label)
        if not self.level_2 and self.num_required >= 2\
                and not self.hide_level_2:
            label = labels.get('level_2', 'level_2')
            raise ValidationError(_("The field %s is required") % label)
        if not self.level_3 and self.num_required >= 3\
                and not self.hide_level_3:
            label = labels.get('level_3', 'level_3')
            raise ValidationError(_("The field %s is required") % label)
        if not self.level_4 and self.num_required >= 4\
                and not self.hide_level_4:
            label = labels.get('level_4', 'level_4')
            raise ValidationError(_("The field %s is required") % label)
        if not self.level_5 and self.num_required >= 5\
                and not self.hide_level_5:
            label = self.fields_get('level_5').get('level_5', {}).\
                get('string', 'level_5')
            raise ValidationError(_("The field %s is required") % label)

    def find_level(self, category, level):
        parent = category
        while parent:
            if parent.level_parents == level:
                return parent
            parent = parent.parent_id
        return False

    def _compute_allow_categ_ids(self):
        model, res_id = self.get_model_and_id()
        obj_id = self.env[model].browse(res_id)
        if not obj_id:
            raise UserError(
                _("There is not a %s selected,"
                  " please click on Edit button again") % model)

        cat_obj = self.get_object()
        self.allow_categ_ids = cat_obj.search([('parent_id', '=', False)])

    @api.onchange('allow_categ_ids')
    def _onchange_allow_categ_ids(self):
        domain = [('parent_id', '=', False)]
        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: not x.parent_id)
            if self.init_category_id:
                self.level_1 = self.find_level(self.init_category_id, 1)
            elif len(allow_categ) == 1:
                if not self.init_category_id:
                    self.level_1 = allow_categ
                return {}
            domain += [('id', 'in', self.allow_categ_ids.ids)]
        return {'domain': {'level_1': domain}}

    @api.onchange('level_1')
    def _onchange_level_1(self):
        self.level_2 = False
        if not self.level_1:
            return {}
        domain = [('parent_id', '=', self.level_1.id)]
        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: x.parent_id == self.level_1)
            if self.init_category_id:
                self.level_2 = self.find_level(self.init_category_id, 2)
            elif len(allow_categ) == 1:
                if not self.init_category_id:
                    self.level_2 = allow_categ
                domain += [('id', 'in', self.allow_categ_ids.ids)]
            elif len(allow_categ) > 1:
                domain += [('id', 'in', self.allow_categ_ids.ids)]
        self.hide_level_2 = bool(not self.level_2.search_count(domain))
        return {'domain': {'level_2': domain}}

    @api.onchange('level_2')
    def _onchange_level_2(self):
        self.level_3 = False
        if not self.level_2:
            return {}
        domain = [('parent_id', '=', self.level_2.id)]
        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: x.parent_id == self.level_2)
            if self.init_category_id:
                self.level_3 = self.find_level(self.init_category_id, 3)
            elif len(allow_categ) == 1:
                if not self.init_category_id:
                    self.level_3 = allow_categ
                domain += [('id', 'in', self.allow_categ_ids.ids)]
            elif len(allow_categ) > 1:
                domain += [('id', 'in', self.allow_categ_ids.ids)]
        self.hide_level_3 = bool(not self.level_3.search_count(domain))
        return {'domain': {'level_3': domain}}

    @api.onchange('level_3')
    def _onchange_level_3(self):
        self.level_4 = False
        if not self.level_3:
            return {}
        domain = [('parent_id', '=', self.level_3.id)]
        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: x.parent_id == self.level_3)
            if self.init_category_id:
                self.level_4 = self.find_level(self.init_category_id, 4)
            elif len(allow_categ) == 1:
                if not self.init_category_id:
                    self.level_4 = allow_categ
                domain += [('id', 'in', self.allow_categ_ids.ids)]
            elif len(allow_categ) > 1:
                domain += [('id', 'in', self.allow_categ_ids.ids)]
        self.hide_level_4 = bool(not self.level_4.search_count(domain))
        return {'domain': {'level_4': domain}}

    @api.onchange('level_4')
    def _onchange_level_4(self):
        self.level_5 = False
        if not self.level_4:
            return {}
        domain = [('parent_id', '=', self.level_4.id)]
        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: x.parent_id == self.level_4
            )
            if self.init_category_id:
                self.level_5 = self.find_level(self.init_category_id, 5)
            elif len(allow_categ) == 1:
                if not self.init_category_id:
                    self.level_5 = allow_categ
                domain += [('id', 'in', self.allow_categ_ids.ids)]
            elif len(allow_categ) > 1:
                domain += [('id', 'in', self.allow_categ_ids.ids)]
        self.hide_level_5 = bool(not self.level_5.search_count(domain))
        return {'domain': {'level_5': domain}}

    def save_category(self):
        self.levels_contraints()
        model, res_id = self.get_model_and_id()
        obj_id = self.env[model].browse(res_id)
        if not obj_id:
            raise UserError(
                _("There is not a %s select,"
                  " please clic on Edit button again") % model)
        field = self._context.get('field_to_write', False) or 'categ_id'
        categ_id = self.level_5 or self.level_4 or self.level_3 or \
            self.level_2 or self.level_1
        if categ_id:
            value = [(4, categ_id.id)
                     ] if self._context.get('many2many_field') else categ_id.id
            obj_id.write({field: value})
        view_id = self._context.get('view_back_ref')
        if view_id:
            view_id = self.env.ref(view_id)
            return {
                'name': 'Odoo',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': view_id.id,
                'res_id': obj_id.id,
                'res_model': view_id.model,
                'target': 'new',
            }

    def cancel(self):
        view_id = self._context.get('view_back_ref')
        if view_id:
            model, res_id = self.get_model_and_id()
            obj_id = self.env[model].browse(res_id)
            if obj_id:
                view_id = self.env.ref(view_id)
                return {
                    'name': 'Odoo',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': view_id.id,
                    'res_id': obj_id.id,
                    'res_model': view_id.model,
                    'target': 'new',
                }
        return {'type': 'ir.actions.act_window_close'}
