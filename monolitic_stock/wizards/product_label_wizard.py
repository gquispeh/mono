# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https: //www.gnu.org/licenses/agpl).

from odoo import fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductLabelWizard(models.TransientModel):
    _name = 'product.label.wizard'
    _description = 'Wizard for set up and print a product label'

    def _default_reference(self):
        if self._context.get('active_model') in [
                'product.template', 'product.product']:
            return self.env[self._context['active_model']].browse(
                self._context['active_id']).default_code
        elif self._context.get('active_model') == 'stock.move':
            return self.env[self._context['active_model']].browse(
                self._context['active_id']).product_id.default_code

    def _default_uom(self):
        if self._context.get('active_model') in [
                'product.template', 'product.product']:
            return self.env[self._context['active_model']].browse(
                self._context['active_id']).uom_id.id
        elif self._context.get('active_model') == 'stock.move':
            return self.env[self._context['active_model']].browse(
                self._context['active_id']).product_id.uom_id.id

    def _default_fifo(self):
        if self._context.get('active_model') == 'stock.move':
            return self.env[self._context['active_model']].browse(
                self._context['active_id']).quant_sequence_fifo
        else:
            return ''

    reference = fields.Char(default=_default_reference)
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        default=_default_uom,
    )
    label_qty = fields.Integer(string='Qty Labels', default=1)
    qty_package = fields.Integer()
    product_id = fields.Many2one(comodel_name='product.product')
    product_tmpl_id = fields.Many2one(comodel_name='product.template')
    move_id = fields.Many2one(comodel_name='stock.move',)
    fifo = fields.Char(default=_default_fifo)
