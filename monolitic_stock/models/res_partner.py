# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    monolitic_supplier_code = fields.Char(string='Supplier Number')
    reservation_orderpoint_count = fields.Integer(
        compute="_compute_reservation_orderpoint")
    reservation_orderpoint_ids = fields.One2many(
        comodel_name='stock.orderpoint.reservation',
        inverse_name='partner_id')
    not_valued_picking = fields.Boolean(
        string='Not valued picking',
    )
    prohibited_partial_shippings = fields.Boolean(
        string='Prohibited partial shippings',
    )
    logistic_customer_tag = fields.Boolean(
        string='Logistic customer tag'
    )
    logistic_customer_tag_type = fields.Selection(
        string='Logistic customer tag type',
        selection=[
            ("barcode", "Código de barras"),
            ("barcode_expanded", "Código de barras desglosado"),
            ("barcode_qr", "Código QR"),
            ("special_tag", "Etiqueta especial"),
            ("manual_printing_packages", "Impresión manual x bultos"),
        ],
    )
    delivery_conditions_id = fields.Many2one(
        string='Delivery carrier',
        comodel_name='stock.delivery.condition',
    )
    property_delivery_carrier_id = fields.Many2one(
        string='Delivery conditions'
    )

    def open_reservation_orderpoint(self):
        self.ensure_one()
        action = self.env.ref(
            'monolitic_stock.stock_orderpoint_reservation_action').read()[0]
        action['domain'] = [('id', 'in', self.reservation_orderpoint_ids.ids)]
        return action

    def _compute_reservation_orderpoint(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        for rec in self:
            rec.reservation_orderpoint_count = 0

        all_partners = self.search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        sale_order_groups = self.env['stock.orderpoint.reservation']\
            .read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            fields=['partner_id'], groupby=['partner_id']
        )
        for group in sale_order_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.reservation_orderpoint_count += group[
                        'partner_id_count']
                partner = partner.parent_id
