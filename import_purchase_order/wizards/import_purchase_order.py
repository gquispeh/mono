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


class ImportPurchaseOrder(models.Model):
    _name = 'import.purchase.order'
    _description = 'Import PO Wizard'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )
    import_type = fields.Selection(
        string='Type',
        selection=[('purchase.order', 'Purchase Order'),
                   ('purchase.order.line', 'Purchase Order Line')],
        default="purchase.order")
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

    def search_obj(self, obj, value, many=False, field="name", op='='):
        record = self.env[obj].search([(field, op, value)])
        if many:
            return record.ids if record else False
        else:
            return record[0].id if record else False

    def _prepare_purchase_line_values(self, values):
        if 'product_id' in values:
            product_id = self.with_context(active_test=False).search_obj(
                'product.product', values['product_id'], field='default_code')
            if not product_id:
                raise UserError(_("Product %s don't found!") % values['product_id'])
            values['product_id'] = product_id

        if 'intrastat_transport_mode_id' in values:
            if values['intrastat_transport_mode_id']:
                values['intrastat_transport_mode_id'] = self.search_obj(
                    'account.intrastat.code', values['intrastat_transport_mode_id'])

        if not values['requested_shipping_date']:
            del values['requested_shipping_date']

        if not values['commitment_date']:
            del values['commitment_date']

        if not values['date_planned']:
            del values['date_planned']

        if 'price_unit' in values:
            values['price_unit'] = values['price_unit'].replace(',', '.')

        del values['sequence2']

        return values

    def _import_purchase_order_line(self, values, update):
        purchase_obj = self.env['purchase.order'].search(
            [('name', '=', values['id_pedido'])])
        if not purchase_obj:
            raise UserError(
                _("Purchase order not found: %s" % values['name']))
        values.pop('id_pedido')

        if purchase_obj:
            # order_line_obj = self.env['purchase.order.line'].search([
            #     ('order_id', '=', purchase_obj.id),
            #     ('product_id', '=', values['product_id']),
            # ])
            # if order_line_obj and not update:
            #     return (
            #         "Order Line %s already exists." % order_line_obj.name)

            values = self._prepare_purchase_line_values(values)
            values['order_id'] = purchase_obj.id

            # if order_line_obj:
            #     order_line_obj.write(values)
            #     return "Order Line %s updated." % order_line_obj.name
            # else:
            order_line_obj = self.env['purchase.order.line'].create(values)
            return "Order Line %s created." % order_line_obj.name

    def _import_purchase_order(self, values, update):
        if 'partner_id' in values:
            partner_id = self.env['res.partner'].with_context(
                active_test=False).search([(
                    'ref', '=', values['partner_id'])])
            values['partner_id'] = partner_id.id
            values['currency_id'] = partner_id.property_purchase_currency_id.id
            values['imported'] = True
            if not partner_id:
                raise UserError(_("Supplier not found: %s" % values['partner_id']))

        purchase_obj = self.env['purchase.order'].search([
            ('name', '=', values['name'])])
        values['state'] = 'sent'

        _logger.info('VALUES')
        _logger.info(values)

        if purchase_obj and not update:
            return "Purchase Order %s already exists." % purchase_obj.name

        if purchase_obj:
            purchase_obj.with_context(import_write=True).write(values)
            return "Purchase Order %s updated." % purchase_obj.name
        else:
            purchase_obj = purchase_obj.create(values)
            return "Purchase Order %s created." % purchase_obj.name

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
            if temp == '\ufeff"name"':
                temp = 'name'
            keys.append(temp)
        _logger.info('The keys of the file are: ')
        _logger.info(keys)
        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    if self.import_type == "purchase.order":
                        if self.use_jobs:
                            self.with_delay()._import_purchase_order(
                                values, self.update)
                        else:
                            self._import_purchase_order(values, self.update)
                    else:
                        if self.use_jobs:
                            self.with_delay()._import_purchase_order_line(
                                values, self.update)
                        else:
                            self._import_purchase_order_line(values, self.update)
        return {'type': 'ir.actions.act_window_close'}
