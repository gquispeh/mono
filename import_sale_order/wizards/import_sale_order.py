# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# Copyright 2019 Aleix de la rubia <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportSaleOrder(models.Model):
    _name = 'import.sale.order'
    _description = 'Import SO Wizard'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )
    import_type = fields.Selection(
        string='Type',
        selection=[('sale.order', 'Sale Order'),
                   ('sale.order.line', 'Sale Order Line')],
        default="sale.order")
    update = fields.Boolean()
    use_jobs = fields.Boolean(default=True)

    def santinize_val(self, values):
        i, x = [0, values[0]]
        while x == ' ':
            i, x = [i + 1, values[i + 1]]
        j, x = [len(values), values[-1]]
        while x == ' ':
            j, x = [j - 1, values[j - 2]]
        return values[i:j]

    def _prepare_sale_line_values(self, values):
        keys_miss_list = []
        for k, v in values.items():
            if v == "":
                keys_miss_list.append(k)
            elif v in ["True", "False"]:
                values[k] = eval(v)
            elif v == "Sí":
                values[k] = True
            elif v == "No":
                values[k] = False
        for key in keys_miss_list:
            values.pop(key)

        if 'product_id' in values:
            product_id = self.with_context(active_test=False).search_obj(
                'product.product', values['product_id'], field='default_code')
            if not product_id:
                raise UserError(_("Product %s don't found!") % values['product_id'])
            values['product_id'] = product_id

        if 'client_segmentation_id' in values:
            # segmentation = values['client_segmentation_id'].replace('/', ' / ')
            values['client_segmentation_id'] = self.search_obj(
                'monolitic.client.segmentation', values['client_segmentation_id'], field='complete_name')
            # if not values['client_segmentation_id']:
            #     raise UserError(_("You cannot create a sale order line without client segmentation!"))

        if 'product_uom' in values:
            values['product_uom'] = self.with_context(lang='es_ES').search_obj(
                'uom.uom', values['product_uom'])

        if 'pricelist_price' in values:
            values['pricelist_price'] = values['pricelist_price'].replace('.', '')
            values['pricelist_price'] = values['pricelist_price'].replace(',', '.')


        # if 'purchase_price' in values:
        #     values['purchase_price'] = values['purchase_price'].replace(',', '.')

        if 'price_unit' in values:
            values['price_unit'] = values['price_unit'].replace('.', '')
            values['price_unit'] = values['price_unit'].replace(',', '.')

        if 'pricelist_discount' in values:
            values['pricelist_discount'] = values['pricelist_discount'].replace('.', '')
            values['pricelist_discount'] = values['pricelist_discount'].replace(',', '.')

        if 'tax_id' in values:
            tax_ids = self.with_context(lang='es_ES').search_obj('account.tax',
                                      list(map(lambda x: self.santinize_val(
                                          x), values['tax_id'].split(','))),
                                      True, 'name', 'in')
            values['tax_id'] = [(6, 0, tax_ids)] if tax_ids else False

        return values

    def _import_sale_order_line(self, values, update):
        sale_obj = self.env['sale.order'].search(
            [('name', '=', values['id_pedido'])])
        if not sale_obj:
            raise UserError(
                _("Sale order not found: %s" % values['id_pedido']))
        del values['id_pedido']

        if sale_obj:
            order_line_obj = self.env['sale.order.line'].search([
                ('order_id', '=', sale_obj.id),
                ('sequence', '=', values['sequence']),
            ])
            if order_line_obj and not update:
                return (
                    "Order Line %s already exists." % order_line_obj.name)

            values = self._prepare_sale_line_values(values)
            values['order_id'] = sale_obj.id

            _logger.info('VALUES')
            _logger.info(values)

            if order_line_obj:
                order_line_obj.write(values)
                return "Order Line %s updated." % order_line_obj.name
            else:
                order_line_obj = order_line_obj.create(values)
                return "Order Line %s created." % order_line_obj.name

    def search_obj(self, obj, value, many=False, field="name", op='='):
        record = self.env[obj].search([(field, op, value)])
        if many:
            return record.ids if record else False
        else:
            return record[0].id if record else False

    def _prepare_sale_order_values(self, values):
        keys_miss_list = []
        for k, v in values.items():
            if v == "":
                keys_miss_list.append(k)
            elif v in ["True", "False"]:
                values[k] = eval(v)
            elif v == "Sí":
                values[k] = True
            elif v == "No":
                values[k] = False
        for key in keys_miss_list:
            values.pop(key)

        if 'partner_id' in values:
            if values['partner_id']:
                customer_id = self.with_context(active_test=False).search_obj(
                    'res.partner', values['partner_id'], field='ref')
                if not customer_id:
                    raise UserError(_("Customer %s don't found!") %
                                    values['partner_id'])
                values['partner_id'] = customer_id
                values['partner_invoice_id'] = customer_id
                values['partner_shipping_id'] = customer_id

        if 'opportunity_id' in values:
            if values['opportunity_id']:
                opportunity_id = self.with_context(active_test=False).search_obj(
                    'crm.lead', values['opportunity_id'], field='code')
                if not opportunity_id:
                    opportunity_id = False
                values['opportunity_id'] = opportunity_id

        if 'quotation_id' in values:
            if values['quotation_id']:
                quotation_id = self.search_obj(
                    'sale.order', values['quotation_id'], False)
                if not quotation_id:
                    quotation_id = False
                values['quotation_id'] = quotation_id

        if 'pricelist_id' in values:
            if values['pricelist_id']:
                currency = self.env['res.currency'].search([(
                        'name', '=', values['pricelist_id'])])
                pricelist = self.env['product.pricelist'].search([
                    ('currency_id', '=', currency.id)], limit=1)
                if pricelist:
                    values['pricelist_id'] = pricelist.id
                else:
                    values['pricelist_id'] = self.env.ref('product.list0').id

        if 'payment_term_id' in values:
            if values['payment_term_id']:
                values['payment_term_id'] = self.with_context(lang='es_ES').search_obj(
                    'account.payment.term', values['payment_term_id'])

        if 'payment_mode_id' in values:
            if values['payment_mode_id']:
                values['payment_mode_id'] = self.with_context(lang='es_ES').search_obj(
                    'account.payment.mode', values['payment_mode_id'])

        if 'fiscal_position_id' in values:
            if values['fiscal_position_id']:
                values['fiscal_position_id'] = self.with_context(lang='es_ES').search_obj(
                    'account.fiscal.position', values['fiscal_position_id'])

        if 'delivery_conditions_id' in values:
            if values['delivery_conditions_id']:
                values['delivery_conditions_id'] = self.with_context(lang='es_ES').search_obj(
                    'stock.delivery.condition', values['delivery_conditions_id'])

        if 'property_delivery_carrier_id' in values:
            if values['property_delivery_carrier_id']:
                values['carrier_id'] = self.with_context(lang='es_ES').search_obj(
                    'delivery.carrier', values['property_delivery_carrier_id'])
                del values['property_delivery_carrier_id']

        if 'analytic_account_id' in values:
            if values['analytic_account_id']:
                values['analytic_account_id'] = self.with_context(lang='es_ES').search_obj(
                    'account.analytic.account', values['analytic_account_id'])

        if 'user_id' in values:
            values['user_id'] = self.with_context(active_test=False).search_obj(
                'res.users', values['user_id'])
            if not values['user_id']:
                raise UserError(_("You cannot create a sale order without commercial!"))

        if 'campaign_id' in values:
            if values['campaign_id']:
                values['campaign_id'] = self.with_context(lang='es_ES').search_obj(
                    'utm.campaign', values['campaign_id'])

        if 'medium_id' in values:
            if values['medium_id']:
                values['medium_id'] = self.with_context(lang='es_ES').search_obj(
                    'utm.medium', values['medium_id'])

        if 'source_id' in values:
            if values['source_id']:
                values['source_id'] = self.with_context(lang='es_ES').search_obj(
                    'utm.source', values['source_id'])

        if 'tag_ids' in values:
            if values['tag_ids']:
                tag_ids = self.search_obj('crm.tag', values['tag_ids'], True)
                values['tag_ids'] = [(6, 0, tag_ids)] if tag_ids else False
            else:
                del values['tag_ids']

        if 'validity_date' in values:
            if not values['validity_date']:
                del values['validity_date']

        if 'date_order' in values:
            if not values['date_order']:
                del values['date_order']

        if 'commitment_date' in values:
            if not values['commitment_date']:
                del values['commitment_date']

        if 'warehouse_id' in values:
            if values['warehouse_id']:
                values['warehouse_id'] = self.search_obj('stock.warehouse', values['warehouse_id'], op='ilike')

        if 'purchase_currency_id' in values:
            if values['purchase_currency_id']:
                values['purchase_currency_id'] = self.search_obj('res.currency', values['purchase_currency_id'])

        if 'rate' in values:
            values['rate'] = values['rate'].replace(',', '.')

        if 'cancel_reason_id' in values:
            if values['cancel_reason_id']:
                values['cancel_reason_id'] = self.with_context(lang='es_ES').search_obj('sale.order.cancel.reason', values['cancel_reason_id'])

        if 'status' in values:
            if values['status'] == 'lost':
                values['state'] = 'cancel'
            del values['status']

        values['imported'] = True

        return values

    def _import_sale_order(self, values, update):
        sale_obj = self.env['sale.order'].search([
            ('name', '=', values['name'])])

        if sale_obj and not update:
            return "Sale Order %s already exists." % sale_obj.name

        values = self._prepare_sale_order_values(values)

        if sale_obj:
            sale_obj.with_context(import_write=True).write(values)
            return "Sale Order %s updated." % sale_obj.name
        else:
            _logger.info('VALUES')
            _logger.info(values)
            sale_obj = sale_obj.with_context(import_create=True).create(values)
            return "Sale Order %s created." % sale_obj.name

    def action_import(self):
        """Load Inventory data from the CSV file."""
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(self.data).decode('utf-8')
        file_input = StringIO(data)
        file_input.seek(0)

        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(
            file_input, delimiter=delimeter, lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]

        # Get column names
        keys_init = reader_info[0]
        keys = []
        for k in keys_init:
            temp = k.replace(' ', '_')
            keys.append(temp)
        _logger.info('The keys of the file are: ')
        _logger.info(keys)
        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            # Don't read rows that start with ( , ' ' or are empty
            if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                if self.import_type == "sale.order":
                    if self.use_jobs:
                        self.with_delay(priority=1)._import_sale_order(
                            values, self.update)
                    else:
                        self._import_sale_order(values, self.update)
                else:
                    if self.use_jobs:
                        self.with_delay(priority=10)._import_sale_order_line(
                            values, self.update)
                    else:
                        self._import_sale_order_line(values, self.update)
        return {'type': 'ir.actions.act_window_close'}
