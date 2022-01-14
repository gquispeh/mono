# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lead_time = fields.Integer(string='Lead Time')
    lead_time_type = fields.Selection(
        string='Lead Time',
        selection=[
            ('day', 'Day(s)'),
            ('week', 'Week(s)'),
            ('month', 'Month(s)'),
            ('year', 'Year(s)')],
        default='day',
    )
    incoming_inspection = fields.Boolean(
        string='Incoming Inspection',
        required=True,
        default=False,
    )
    rohs_regulation = fields.Boolean(
        string='RoHS regulation',
        required=True,
        default=False,
    )
    supplier_internal_ref = fields.Char(
        string='Supplier Internal Reference',
    )

    @api.onchange('seller_ids')
    def onchange_seller_ids(self):
        for product in self:
            if not product.warranty and product.seller_ids:
                product.warranty = product.seller_ids[-1].warranty
                product.warranty_type = product.seller_ids[-1].warranty_type
            if not product.lead_time and product.seller_ids:
                product.lead_time = product.seller_ids[-1].lead_time
                product.lead_time_type = product.seller_ids[-1].lead_time_type


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    warranty = fields.Integer(
        related='name.warranty',
        string='Warranty Duration',
        readonly=True,
    )
    warranty_type = fields.Selection(
        related='name.warranty_type',
        string='Warranty Type',
        readonly=True,
    )
    lead_time = fields.Integer(
        related='name.lead_time',
        string='Lead Time',
        readonly=True,
    )
    lead_time_type = fields.Selection(
        related='name.lead_time_type',
        string='Lead Time Type',
        readonly=True,
    )
    observations = fields.Text(
        string='Observations',
    )
    active = fields.Boolean(default=True)
    product_code = fields.Char(
        'Vendor Product Code',
    )
