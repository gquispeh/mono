# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https: //www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    served_products = fields.Float(
        compute='compute_served_products', string="Served Products")

    def compute_served_products(self):
        for partner in self:
            all_partners = self.with_context(active_test=False).search([
                ('id', 'child_of', partner.ids)])
            all_partners.read(['parent_id'])

            sale_line_obj = self.env['sale.order.line'].search([
                ('order_partner_id', 'in', all_partners.ids)])
            partner.served_products = sum(sale_line_obj.mapped('product_qty'))

    def action_view_served_product_sales(self):
        self.ensure_one()
        all_partners = self.with_context(active_test=False).search([
            ('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        sale_line_ids = self.env['sale.order.line'].search([
            ('order_partner_id', 'in', all_partners.ids)]).ids

        tree_view_id = self.env.ref('sale.view_order_line_tree').id
        form_view_id = self.env.ref(
            'sale.sale_order_line_view_form_readonly').id
        return {
            'name': 'Served Products',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree, form',
            'res_model': 'sale.order.line',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': [('id', 'in', list(sale_line_ids))],
            'context': {},
        }
