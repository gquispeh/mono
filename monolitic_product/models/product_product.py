# Copyright 2020 Daniel López <daniel.lopez@qubiq.es>
# License AGPL-3.0 or later (https: //www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        prices = dict.fromkeys(self.ids, 0.0)
        if price_type == 'trade_margin':
            for product in self:
                prices[product.id] += product.price_extra
                if self._context.get('no_variant_attributes_price_extra'):
                    prices[product.id] += sum(self._context.get('no_variant_attributes_price_extra'))
            return prices
        else:
            return super(ProductProduct, self).price_compute(price_type, uom=False, currency=False, company=None)

    def generate_qr(self):
        qr_image = 0
        if self.barcode:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.barcode)
            qr.make(fit=True)

            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
        return qr_image

    def get_sale_ids(self):
        done_states = self.env['sale.report']._get_done_states()
        done_states.extend(['sale_to_acuse', 'pending_payment', 'sale_confirmed'])
        ids = self.env['sale.order.line'].search([
            ('state', 'in', done_states),
            ('product_id', 'in', self.ids)
        ]).ids
        return ids

    def get_purchase_ids(self):
        ids = self.env['purchase.order.line'].search([
            ('state', 'in', ['purchase', 'done']),
            ('product_id', 'in', self.ids)
        ]).ids
        return ids

    def action_custom_sale_view(self):
        self.ensure_one()
        ids = set()
        for p in self.with_context(active_test=False):
            ids |= set(p.get_sale_ids())
        tree_view_id = self.env.ref('sale.view_order_line_tree').id
        form_view_id = self.env.ref(
            'sale.sale_order_line_view_form_readonly').id
        return {
            'name': 'Ventas por producto',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'sale.order.line',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': [('id', 'in', list(ids))],
            'context': {},
        }

    def action_custom_purchase_view(self):
        self.ensure_one()
        ids = set()
        for p in self.with_context(active_test=False):
            ids |= set(p.get_purchase_ids())
        tree_view_id = self.env.ref('purchase.purchase_order_line_tree').id
        form_view_id = self.env.ref('purchase.purchase_order_line_form2').id
        return {
            'name': 'Compras por producto',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'purchase.order.line',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': [('id', 'in', list(ids))],
            'context': {},
        }
