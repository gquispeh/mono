# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError


class ClientSegmentation(models.Model):
    _name = "monolitic.client.segmentation"
    _description = "Segmentación cliente"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Name', index=True,
                       required=True, translate=True)
    complete_name = fields.Char(
        "Complete name", compute='_compute_complete_name',
        store=True, readonly=True)
    parent_id = fields.Many2one(
        'monolitic.client.segmentation', 'Parent Segmentation', index=True,
        ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many(
        'monolitic.client.segmentation', 'parent_id', 'Child Categories')

    level_parents = fields.Integer(
        compute='_compute_level_parents',
        search='_search_level_parents',
        store=True)

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
        ids = self.env['monolitic.client.segmentation'].search([]).\
            filtered(f).ids
        return [('id', 'in', ids)]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (
                    category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(('You cannot create recursive categories.'))
        return True

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
    
    def unlink(self):
        for rec in self:
            clients = self.env['res.partner'].search([
                '|',('segmentation_ids', 'in', [rec.id]),
                ('segmentation_ids', 'in', rec.child_id.ids)
            ])
            if clients:
                raise UserError(
                    _('You cannot delete this client segmentation if there are clients'
                        ' associated with it or with its child!')
                )
        return super(ClientSegmentation, self).unlink()
