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


class ImportCustomerProduct(models.TransientModel):
    _name = "import.customer.product"
    _description = "Import Customer Product"

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter ","',
    )

    def _create_customer_product(self, values):
        customer_product_obj = self.env['product.customerinfo']

        if values['name']:
            customer_obj = self.env['res.partner'].with_context(
                active_test=False).search([
                    ('ref', '=', values['name']),
                    ('parent_id', '=', False),
                ])
            if not customer_obj:
                raise UserError("Customer not found! %s" % values['name'])

        if values['product_tmpl_id']:
            product_tmpl_obj = self.env['product.template'].with_context(
                active_test=False).search([
                    ('default_code', '=', values['product_tmpl_id']),
                ])
            if not product_tmpl_obj:
                raise UserError(
                    "Product not found! %s" % values['product_tmpl_id'])

        if customer_obj and product_tmpl_obj:
            cus_prod_vals = {
                'name': customer_obj.id,
                'product_tmpl_id': product_tmpl_obj.id,
                'product_code': values['product_code'],
            }
            customer_product_obj = customer_product_obj.create(cus_prod_vals)

            _logger.info(
                "Created Customer Product: %s",
                customer_product_obj.product_code)
            return True

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
                    self._create_customer_product(values)

        return {'type': 'ir.actions.act_window_close'}
