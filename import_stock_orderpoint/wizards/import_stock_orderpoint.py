# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import base64
import csv
from io import StringIO
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ImportStockOrderpoint(models.Model):
    _name = 'import.stock.orderpoint'
    _description = 'Import Stock Orderpoint'

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
        if values['security_stock']:
            values['security_stock'] = values[
                'security_stock'].replace('.', '')
            values['security_stock'] = values[
                'security_stock'].replace(',', '.')
        return values

    '''
        Function to create the stock orderpoint.

        :param values: Dict with the values to import.
    '''
    def _create_new_stock_orderpoint(self, values,):
        values = self._update_values(values)

        location_id = self.env['stock.location'].search([(
            'complete_name', '=', values['location_id']
        )])
        if not location_id:
            raise UserError(
                "No se encuentra la ubicación %s" % values['location_id'])

        product_id = self.env[
            'product.product'].with_context(active_test=False).search([
                ('default_code', '=', values['product_code'])
            ])
        if not product_id:
            raise UserError(
                "No se encuentra el producto %s" % values['product_id'])

        stock_orderpoint_obj = self.env['stock.warehouse.orderpoint'].search([
            ('name', '=', values['name'])
        ])
        vals = {
            'name': values['name'],
            'warehouse_id': 1,
            'location_id': location_id.id,
            'product_id': product_id.id,
            'security_stock': values['security_stock'],
            'product_max_qty': 0.00,
            'qty_multiple': 1,
            'company_id': self.env.user.company_id.id,
        }
        if stock_orderpoint_obj:
            stock_orderpoint_obj.sudo().write(vals)
            stock_orderpoint_obj._compute_product_min_qty()
        else:
            stock_orderpoint_obj = self.env[
                'stock.warehouse.orderpoint'].sudo().create(vals)
            stock_orderpoint_obj._compute_product_min_qty()
            self.env['ir.sequence'].next_by_code('stock.orderpoint')

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
                UPDATE stock_warehouse_orderpoint
                SET create_date = %s, create_uid = %s
                WHERE id = %s
            """, (values['create_date'], user_obj.id, str(stock_orderpoint_obj.id)))
            # created_message = self.env['mail.message'].sudo().search([
            #     ('res_id', '=', stock_orderpoint_obj.id),
            #     ('model', '=', 'res.partner'),
            # ], order='id asc', limit=1)
            # if created_message:
            #     self._cr.execute("""
            #         UPDATE mail_message
            #         SET date = %s, author_id = %s
            #         WHERE id = %s
            #     """, (values['create_date'], user_obj.id, str(created_message.id)))

        return stock_orderpoint_obj

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
            if temp == '\ufeff"name"':
                temp = 'name'
            keys.append(temp)
        _logger.info('The keys of the file are: ')
        _logger.info(keys)
        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            if reader_info[i]:
                field = reader_info[i]
                values = dict(zip(keys, field))
                self.with_delay()._create_new_stock_orderpoint(values)
        return {'type': 'ir.actions.act_window_close'}
