# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from datetime import datetime

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


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    quant_sequence_fifo = fields.Many2many('stock.quant.sequence')
    sale_line = fields.Many2one(
        related="move_id.sale_line_id", readonly=True, string="Related order line"
    )
    currency_id = fields.Many2one(
        related="sale_line.currency_id", readonly=True, string="Sale Currency"
    )
    sale_tax_id = fields.Many2many(
        related="sale_line.tax_id", readonly=True, string="Sale Tax"
    )
    sale_price_unit = fields.Float(
        related="sale_line.price_unit", readonly=True, string="Sale price unit"
    )
    sale_discount = fields.Float(
        related="sale_line.discount", readonly=True, string="Sale discount (%)"
    )
    sale_tax_description = fields.Char(
        compute="_compute_sale_order_line_fields",
        string="Tax Description",
        compute_sudo=True,  # See explanation for sudo in compute method
    )
    sale_price_subtotal = fields.Monetary(
        compute="_compute_sale_order_line_fields",
        string="Price subtotal",
        compute_sudo=True,
    )
    sale_price_tax = fields.Float(
        compute="_compute_sale_order_line_fields",
        string="Taxes",
        compute_sudo=True
    )
    sale_price_total = fields.Monetary(
        compute="_compute_sale_order_line_fields",
        string="Total",
        compute_sudo=True
    )
    client_product_code = fields.Char(compute='_compute_client_product_code')
    sale_line_number = fields.Integer(compute='_compute_sale_line_number')

    def generate_qr(self):
        qr_image = 0
        if self.lot_id:
            lot = self.lot_id.name
        else:
            lot = ''

        qr_string = '[MPN]'+str(self.product_id.default_code) + ' ' + \
            '[MLC]' + lot + ' ' + '[MDC]' + \
            str(self.picking_id.scheduled_date.date()) + \
            ' ' + '[IPN]' + str(self.client_product_code) + ' ' + \
            '[QTY]' + str(self.qty_done)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        return qr_image

    def _compute_sale_line_number(self):
        for rec in self:
            rec.sale_line_number = False
            if rec.picking_id.sale_id:
                rec.sale_line.number

    def _compute_client_product_code(self):
        for rec in self:
            if rec.product_id:
                customer_info = rec.product_id.customer_ids.filtered(
                    lambda x: x.name == rec.picking_id.partner_id)
                if customer_info:
                    rec.client_product_code = customer_info.product_code
                else:
                    rec.client_product_code = False

    def _compute_sale_order_line_fields(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to sales orders (stricter warehouse users, inter-company
        records...).
        """
        for line in self:
            sale_line = line.sale_line
            price_unit = (
                sale_line.price_subtotal / sale_line.product_uom_qty
                if sale_line.product_uom_qty
                else sale_line.price_reduce
            )
            taxes = line.sale_tax_id.compute_all(
                price_unit=price_unit,
                currency=line.currency_id,
                quantity=line.qty_done or line.product_qty,
                product=line.product_id,
                partner=sale_line.order_id.partner_shipping_id,
            )
            if sale_line.company_id.tax_calculation_rounding_method == (
                "round_globally"
            ):
                price_tax = sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
            else:
                price_tax = taxes["total_included"] - taxes["total_excluded"]
            line.update(
                {
                    "sale_tax_description": ", ".join(
                        t.name or t.description for t in line.sale_tax_id
                    ),
                    "sale_price_subtotal": taxes["total_excluded"],
                    "sale_price_tax": price_tax,
                    "sale_price_total": taxes["total_included"],
                }
            )
