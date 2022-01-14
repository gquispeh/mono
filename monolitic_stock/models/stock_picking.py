# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from functools import partial
from odoo.tools.misc import formatLang

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


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'stock.delivery.mixing']

    @api.model
    def create(self, values):
        res = super(StockPicking, self).create(values)
        if res.sale_id:
            if res.sale_id.delivery_conditions_id:
                res.delivery_conditions = res.sale_id.delivery_conditions_id.id
        return res

    @api.model
    def _default_note(self):
        return (self.env['ir.config_parameter'].sudo().
                get_param('picking_order.use_picking_note') and
                self.env.company.picking_note or '')

    picking_note = fields.Html(default=_default_note)
    not_valued_picking = fields.Boolean(
        string='Not valued picking',
        related="sale_id.not_valued_picking",
        readonly=False,
    )
    prohibited_partial_shippings = fields.Boolean(
        string='Prohibited partial shippings',
        related="sale_id.prohibited_partial_shippings",
        readonly=False,
    )
    weight = fields.Float(readonly=False)
    impack_weight = fields.Integer(string='Impack shipping weight')
    is_return = fields.Boolean(string='Return')
    currency_id = fields.Many2one(
        related="sale_id.currency_id",
        readonly=True,
        string="Currency",
        related_sudo=True,  # See explanation for sudo in compute method
    )
    amount_untaxed = fields.Monetary(
        compute="_compute_amount_all",
        string="Untaxed Amount",
        compute_sudo=True,  # See explanation for sudo in compute method
    )
    amount_tax = fields.Monetary(
        compute="_compute_amount_all", string="Taxes", compute_sudo=True
    )
    amount_total = fields.Monetary(
        compute="_compute_amount_all", string="Total", compute_sudo=True
    )
    amount_by_group = fields.Binary(
        string="Tax amount by group",
        compute="_amount_by_group"
    )
    carrier_id = fields.Many2one(
        string='Delivery conditions'
    )

    def _amount_by_group(self):
        for picking in self:
            currency = picking.currency_id or picking.company_id.currency_id
            fmt = partial(formatLang, self.with_context(
                lang=picking.partner_id.lang).env,
                currency_obj=currency)
            picking.amount_by_group = [(
                fmt(tax_group['amount']), tax_group['tax'].tax_group_id.name
            ) for tax_group in picking.get_taxes_values().values()]

    def _compute_amount_all(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to sales orders (stricter warehouse users, inter-company
        records...).
        """
        for pick in self:
            round_curr = pick.sale_id.currency_id.round
            amount_tax = 0.0
            for tax_group in pick.get_taxes_values().values():
                amount_tax += round_curr(tax_group["amount"])
            amount_untaxed = sum(
                line.sale_price_subtotal for line in pick.move_line_ids
            )
            pick.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_tax": amount_tax,
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.move_line_ids:
            for tax in line.sale_line.tax_id:
                tax_id = tax.id
                if tax_id not in tax_grouped:
                    tax_grouped[tax_id] = {"base": line.sale_price_subtotal, "tax": tax}
                else:
                    tax_grouped[tax_id]["base"] += line.sale_price_subtotal
        for tax_id, tax_group in tax_grouped.items():
            tax_grouped[tax_id]["amount"] = tax_group["tax"].compute_all(
                tax_group["base"], self.sale_id.currency_id
            )["taxes"][0]["amount"]
        return tax_grouped

    def _check_backorder(self):
        if self.prohibited_partial_shippings:
            raise UserError(_(
                'Partial deliveries are prohibited for this order !'))

        return super(StockPicking, self)._check_backorder()

    def do_print_picking(self):
        super(StockPicking, self).do_print_picking()
        return self.env.ref(
            'monolitic_stock.ml_report_stock_delivery_document').report_action(self)

    def generate_qr(self):
        qr_image = 0
        if self.name:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.name)
            qr.make(fit=True)

            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
        return qr_image


class StockPickingLine(models.Model):
    _inherit = 'stock.move'

    number = fields.Integer(
        compute='_compute_get_number',
        store=True,
    )

    @api.depends('sequence', 'picking_id')
    def _compute_get_number(self):
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_lines:
                line.number = number
                number += 1

    def get_serial_numbers(self):
        self.ensure_one()
        serial_numbers = self.mapped('move_line_ids')
        if not serial_numbers:
            return ""
        serial_numbers = serial_numbers.mapped('lot_id')
        if not serial_numbers:
            return ""
        serial_numbers = serial_numbers.mapped('name')
        serial_numbers.sort()
        if len(serial_numbers) == 1:
            return serial_numbers[0]
        elif (int(serial_numbers[-1]) - int(serial_numbers[0])
              == len(serial_numbers) - 1):
            return _("from %s to %s") % (serial_numbers[0], serial_numbers[-1])
        start_serial = 0
        number_list = []
        for i, serial in enumerate(serial_numbers):
            if i == (len(serial_numbers) - 1) and not start_serial:
                number_list.append(serial)
            serial = int(serial)
            if not start_serial:
                start_serial = serial
                continue
            elif serial - start_serial == 1:
                if i == (len(serial_numbers) - 1):
                    number_list.append(_("from %i to %i") % (start_serial,
                                       serial))
                continue
            else:
                if (serial == int(serial_numbers[i-1]) or
                        len(serial_numbers) == 2):
                    number_list += [str(start_serial), str(serial)]
                else:
                    number_list.append(_("from %i to %s") % (start_serial,
                                       serial_numbers[i-1]))
                    number_list.append(str(serial))
                start_serial = 0
        return ", ".join(number_list)
