# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https: //www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

import hashlib


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_property_stock = fields.Many2one(
        string='Default Ubication', comodel_name='stock.location',
    )
    categ_id = fields.Many2one(required=False)
    allow_edit_category = fields.Boolean(
        compute="_compute_allow_edit_category")
    min_sell_qty = fields.Integer(string='Min. sell quantity')
    min_order_qty = fields.Integer(string='Min. order quantity')
    packaging_qty = fields.Char(string='Packaging')
    default_code = fields.Char(copy=True)
    bom_line_ids = fields.One2many(copy=True)
    bom_ids = fields.One2many(copy=True)
    weight = fields.Float(copy=True)
    volume = fields.Float(copy=True)
    customer_ids = fields.One2many(copy=True)
    seller_ids = fields.One2many(copy=True)
    invoice_policy = fields.Selection([
        ('delivery', 'Delivered quantities'),
        ('order', 'Ordered quantities')],
        default='delivery')
    supplier_pricelist_price = fields.Float(
        compute="_compute_supplier_pricelist_price")
    logistic_price = fields.Float(
        compute="_compute_supplier_pricelist_price")

    def _compute_supplier_pricelist_price(self):
        for rec in self:
            supplier_pricelist_price_list = []
            for pricelist in rec.seller_ids:
                if rec.currency_id == pricelist.currency_id:
                    supplier_pricelist_price_list.append(pricelist.price)
                else:
                    price_converted = pricelist.currency_id._convert(
                        pricelist.price, rec.currency_id,
                        self.env.user.company_id, datetime.now())
                    supplier_pricelist_price_list.append(price_converted)

            if supplier_pricelist_price_list:
                rec.supplier_pricelist_price = max(
                    supplier_pricelist_price_list, key=lambda x: float(x))
            else:
                rec.supplier_pricelist_price = 0

            rec.logistic_price = (
                rec.supplier_pricelist_price * (
                    rec.categ_id.estimate_cost / 100)
            )

    @api.constrains('default_code')
    def _check_default_code(self):
        # Raise constraint if default_code already exists
        for rec in self:
            if rec.default_code:
                duplicated_code = self.env['product.template'].search_count([
                    ('default_code', '=', rec.default_code)])

                if duplicated_code > 1:
                    raise ValidationError(_(
                        'The product reference cannot be duplicated!'))

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (copy)", self.name)
        if 'default_code' not in default:
            default['default_code'] = _("%s (copy)", self.default_code)
        return super(ProductTemplate, self).copy(default=default)

    def open_pricelist_rules(self):
        view = super(ProductTemplate, self).open_pricelist_rules()
        domain = [
            '|', '|', '|',
            ('product_tmpl_id', '=', self.id),
            ('product_id', 'in', self.product_variant_ids.ids),
            ('categ_id', '=', self.categ_id.id),
            ('applied_on', '=', '3_global'),
        ]
        view.update({
            'domain': domain,
        })
        return view

    @api.onchange('default_code')
    def _onchange_ref(self):
        if self.default_code:
            ref = self.default_code
            ref_modified = ref.replace(' ', '-')
            ref_modified = ref_modified.replace('/', '-')

            text_to_hash = '30b90af1cad3988be5aad \
            da132e07c479fe40aba1533d28142e7ff1a7c5b9dbc' + ref
            token = hashlib.md5(text_to_hash.encode())
            md5_hash = token.hexdigest()

            self.barcode = (
                'http://server7/qr-almacen/?ref=' +
                ref_modified + '&token=' + md5_hash
            )

    def _compute_allow_edit_category(self):
        for rec in self:
            if rec.type == 'product':
                rec.allow_edit_category = bool(rec.seller_ids)
            else:
                rec.allow_edit_category = True

    @api.onchange('seller_ids')
    def _onchange_seller(self):
        if self.type == 'product':
            self.allow_edit_category = bool(self.seller_ids)
        else:
            self.allow_edit_category = True

    def action_custom_sale_view(self):
        self.ensure_one()
        ids = set()
        for p in self.with_context(active_test=False).product_variant_ids:
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
        for p in self.with_context(active_test=False).product_variant_ids:
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

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        hide = [
            'standard_price'
        ]
        res = super(ProductTemplate, self).fields_get(allfields, attributes=attributes)
        for field in hide:
            if field in res:
                res[field]['searchable'] = False
                res[field]['sortable'] = False
                res[field]['exportable'] = False
        return res
