# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def toggle_active(self):
        for product in self:
            if product.active:
                if product.qty_available:
                    raise ValidationError(_(
                        "The product %s cannot be archived "
                        "because it has stock! ") % (product.name))

                elif product.used_in_bom_count:
                    self.env['mrp.bom.line'].search([(
                        'product_id',
                        'in',
                        product.product_variant_ids.ids
                    )]).unlink()

        return super(ProductTemplate, self).toggle_active()
