# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _
from odoo.exceptions import UserError


import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportProduct(models.Model):
    _name = "import.product"
    _description = "Import Product"

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimiter', default='|',
                            help='Default delimiter ","')
    update = fields.Boolean(default=True)

    '''
        Function to update and correct some values.

        :param values: Dict with the values to import.

        :return Dict with the modified values modifieds.
    '''
    def _update_values(self, values):
        for k, v in values.items():
            if v == 'Sí':
                values[k] = True
            elif v == 'No':
                values[k] = False

        if values.get('standard_price', False):
            standard_price = values['standard_price'].replace('.', '')
            standard_price = standard_price.replace(',', '.')
            values['standard_price'] = float(standard_price)
        if values.get('list_price', False):
            list_price = values['list_price'].replace('.', '')
            list_price = list_price.replace(',', '.')
            values['list_price'] = float(list_price)
        if values.get('min_order_qty', False):
            values['min_order_qty'] = float(
                values['min_order_qty'].replace('.', ''))
        if values.get('min_sell_qty', False):
            values['min_sell_qty'] = float(
                values['min_sell_qty'].replace('.', ''))

        values['company_id'] = 1
        values['sale_line_warn'] = 'no-message'

        if 'event_ok' in values:
            del values['event_ok']

        return values

    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _assign_product_data(self, values):
        product_data = {}
        # Assign or create a category
        if values.get('categ_id', False) and values['categ_id'] != '':
            categ_complete_name = []
            if values.get('categ_parent_1', False) and \
                    values['categ_parent_1'] != '':
                categ_complete_name.append(values['categ_parent_1'])
            if values.get('categ_parent_2', False) and \
                    values['categ_parent_2'] != '':
                categ_complete_name.append(values['categ_parent_2'])
            if values.get('categ_parent_3', False) and \
                    values['categ_parent_3'] != '':
                categ_complete_name.append(values['categ_parent_3'])
            if values.get('categ_parent_4', False) and \
                    values['categ_parent_4'] != '':
                categ_complete_name.append(values['categ_parent_4'])

            categ_complete_name = ' / '.join(categ_complete_name)
            categ_obj = self.env['product.category'].search([('complete_name', 'ilike', categ_complete_name)])

            if not categ_obj:
                raise UserError("No category found with domain %s"
                                % categ_complete_name)
            values.update({
                'categ_id': categ_obj[-1].id,
            })

        del values['categ_parent_1']
        del values['categ_parent_2']
        del values['categ_parent_3']
        del values['categ_parent_4']
        del values['categ_parent_5']

        # Assign or update uom
        del values['uom_id']
        del values['uom_po_id']

        # Assign or update intrastat
        if values.get('intrastat_id', False):
            values['intrastat_id'] = values['intrastat_id'].zfill(8)
            intrastat_obj = self.env['account.intrastat.code'].search([(
                'code', '=', values['intrastat_id'])])
            if intrastat_obj:
                product_data.update({
                    'intrastat_id': intrastat_obj.id,
                })
        del values['intrastat_id']

        # Assign or update manufacturer
        if values.get('manufacturer_id', False):
            manufacturer_obj = self.env['res.partner'].search([
                ('ref', '=', values['manufacturer_id']),
                ('parent_id', '=', False),
            ])
            if manufacturer_obj:
                product_data.update({
                    'manufacturer': manufacturer_obj.id,
                })
        del values['manufacturer_id']

        # Assign or update default_ubication
        if values.get('default_ubication', False):
            default_ubication_obj = self.env['stock.location'].search([(
                'complete_name', '=', values['default_ubication'])])
            if default_ubication_obj:
                product_data.update({
                    'default_property_stock': default_ubication_obj.id,
                })
        del values['default_ubication']

        # Assign or optional_products
        if values["optional_product_ids"]:
            optional_product_ids = []
            for product in values['optional_product_ids'].split(';'):
                if product != '':
                    product_id = self.env['product.template'].search([
                        ('default_code', '=', product)])
                    if product_id:
                        optional_product_ids.append(product_id.id)
            product_data.update({
                'optional_product_ids': [(6, 0, optional_product_ids)]
            })
        del values['optional_product_ids']

        # Assign routes
        if values['route_ids']:
            route_ids = []
            for route in values['route_ids'].split(';'):
                if route != '':
                    route_id = self.env[
                        'stock.location.route'].with_context(
                            lang='es_ES').search([('name', '=', route)])
                    if route_id:
                        route_ids.append(route_id.id)
            product_data.update({
                'route_ids': [(6, 0, route_ids)]
            })
        del values['route_ids']

        # Assign Intrastat country
        if values.get('intrastat_origin_country_id', False):
            country_obj = self.env['res.country'].search([(
                'code', '=', values['intrastat_origin_country_id'])])
            if country_obj:
                product_data.update({
                    'intrastat_origin_country_id': country_obj.id,
                })
        del values['intrastat_origin_country_id']

        # Assign Responsible
        if values.get('responsible_id', False):
            user_obj = self.env['res.users'].with_context(
                lang='es_ES').search([(
                    'name', '=', values['responsible_id'])])
            if user_obj:
                product_data.update({
                    'responsible_id': user_obj.id,
                })
        del values['responsible_id']

        # Assign or update a supplier
        if values.get('supplier_code', False):
            supplier_obj = self.env[
                'res.partner'].search([
                    ('unique_code', '=', values['supplier_code']),
                    ('supplier', '=', True)
                ])
            if supplier_obj:
                new_supplier = True
                product_obj = self.env[
                    'product.template'].search([(
                        'default_code', '=', values['default_code'])
                    ])
                currency_obj = self.env[
                    'res.currency'].search([(
                        'name', '=', values['supplier_currency'])])
                product_sellers = product_obj.seller_ids
                if product_sellers:
                    for seller in product_sellers:
                        if seller.name.unique_code == values['supplier_code']:
                            seller_values = {}
                            seller_values = {
                                'min_qty': values['supplier_min_qty'],
                                'price': values['supplier_price'],
                            }
                            if currency_obj:
                                seller_values.update({
                                    'currency_id': currency_obj.id,
                                })
                            product_data.update({
                                    'seller_ids': [
                                        (1, seller.id, seller_values)],
                            })
                            new_supplier = False
                            break
                if new_supplier:
                    seller_values = {}
                    seller_values = {
                        'name': supplier_obj.id,
                        'min_qty': values['supplier_min_qty'],
                        'price': values['supplier_price'],
                    }
                    if currency_obj:
                        seller_values.update({
                            'currency_id': currency_obj.id,
                        })
                    product_data.update({
                        'seller_ids': [(0, 0, seller_values)],
                    })

            del values['supplier_code']
            del values['supplier_min_qty']
            del values['supplier_price']
            del values['supplier_currency']

        return product_data

    '''
        Function to create or write the product.

        :param values: Dict with the values to import.
    '''
    def _create_new_product(self, values, update):
        values = self._update_values(values)
        # Update existing customers
        current_product = self.env['product.template'].with_context(
            active_test=False).search([
                ('default_code', '=', values['default_code'])])
        if not update and current_product:
            return
        fields = {}
        fields = self._assign_product_data(values)
        _logger.info('===== VALS =====')
        _logger.info(values)
        _logger.info(fields)
        if current_product:
            current_product.write(values)
            _logger.info("Updating product: %s", current_product.name)
        else:
            current_product = current_product.create(values)
            _logger.info("Creating product: %s", current_product.name)

        current_product.write(fields)

    '''
        Function to read the csv file and convert it to a dict.

        :return Dict with the columns and its value.
    '''
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
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
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
            if temp == '\ufeff"default_code"':
                temp = 'default_code'
            keys.append(temp)

        del reader_info[0]
        values = {}

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay(priority=1)._create_new_product(values, self.update)
                    #self._create_new_product(values, self.update)

        return {'type': 'ir.actions.act_window_close'}
