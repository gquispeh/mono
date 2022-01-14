# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import base64
import csv
from io import StringIO
from odoo.exceptions import UserError, ValidationError


import logging
_logger = logging.getLogger(__name__)


class ImportStockCustomerReservation(models.Model):
    _name = 'import.stock.customer.reservation'
    _description = 'Import Stock Customer Reservation'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter ";"',
    )

    '''
        Function to update and correct some values.

        :param values: Dict with the values to import.

        :return Dict with the modified values modifieds.
    '''
    def _update_values(self, values):
        if values['min_quantity']:
            values['min_quantity'] = values[
                'min_quantity'].replace('.', '')
            values['min_quantity'] = values[
                'min_quantity'].replace(',', '.')

        return values

    '''
        Function to create the stock customer reservation.

        :param values: Dict with the values to import.
    '''

    def _create_new_stock_customer_reservation(self, values,):
        values = self._update_values(values)

        partner_id = self.env[
            'res.partner'].with_context(active_test=False).search([
                ('ref', '=', values['partner_ref']),
                ('parent_id', '=', False),
            ])
        if not partner_id:
            raise UserError(
                "No se encuentra el cliente %s" % values['partner_ref'])

        product_id = self.env[
            'product.product'].with_context(active_test=False).search([
                ('default_code', '=', values['product_code'])
            ])
        if not product_id:
            raise UserError(
                "No se encuentra el producto %s" % values['product_id'])

        stock_orderpoint_obj = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', product_id.id)
        ], limit=1)
        if not partner_id:
            raise UserError(
                "No se encuentra la regla de abastecimiento con producto %s" %
                values['product_code'])

        vals = {
            'orderpoint_id': stock_orderpoint_obj.id,
            'partner_id': partner_id.id,
            'min_quantity': values['min_quantity'],
        }

        stock_reservation_obj = self.env[
            'stock.orderpoint.reservation'].sudo().create(vals)
        stock_orderpoint_obj._compute_product_min_qty
        if values.get("create_date", False):
            user = self.env.user
            if values.get("create_user", False):
                result = self.env['res.users'].with_context(
                    active_test=False).search([(
                        'name', '=', values['create_user'])])
                if result:
                    user = result
            user_obj = user

            self._cr.execute("""
                UPDATE stock_orderpoint_reservation
                SET create_date = %s, create_uid = %s
                WHERE id = %s
            """, (values['create_date'], user_obj.id, str(stock_reservation_obj.id)))

        return stock_reservation_obj

    '''
        Function to read the csv file and convert it to a dict.

        :return Dict with the columns and its value.
    '''
    def action_import(self):
        """Load Inventory data from the CSV file."""
        if not self.data:
            raise UserError(_("You need to select a file!"))
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
            raise UserError(_("Not a valid file!"))
        keys = reader_info[0]

        # Get column names
        keys_init = reader_info[0]
        keys = []
        for k in keys_init:
            temp = k.replace(' ', '_')
            if temp == '\ufeff"product_code"':
                temp = 'product_code'
            keys.append(temp)

        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            if reader_info[i]:
                field = reader_info[i]
                values = dict(zip(keys, field))
                self.with_delay()._create_new_stock_customer_reservation(values)
        return {'type': 'ir.actions.act_window_close'}
