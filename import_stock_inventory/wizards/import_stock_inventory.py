# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import base64
import csv
from io import StringIO
from datetime import date
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ImportMrpBom(models.Model):
    _name = 'import.stock.inventory'
    _description = 'Import Stock Inventory'

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
        if values['product_qty']:
            values['product_qty'] = values[
                'product_qty'].replace('.', '')
            values['product_qty'] = values[
                'product_qty'].replace(',', '.')
        return values

    '''
        Function to create the mrp nom.

        :param values: Dict with the values to import.
    '''
    def _create_new_stock_inventory(self, values,):
        values = self._update_values(values)
        if not values['product_code']:
            raise UserError("en una linea falta el product_code")
        if values['product_code']:
            location_obj = self.env['stock.location'].search([(
                'complete_name', '=', values['location_id'])])
            if not location_obj:
                raise UserError(
                    "No se encuentra la ubicación %s" % values['location_id'])

            inventory_name = 'Importación Inventario %s' % (
                fields.Date.context_today(self),
            )
            inventory_obj = self.env['stock.inventory'].search([
                ('filter', '=', 'domain'),
                ('state', 'not in', ['done', 'cancel']),
                ('name', '=', inventory_name),
            ])
            if not inventory_obj:
                inventory_obj = self.env['stock.inventory'].sudo().create({
                    'name': inventory_name,
                    'filter': 'domain',
                })
                inventory_obj.action_start()

            # Search for line
            product_id = self.env['product.product'].search([
                ('default_code', '=', values['product_code'])
            ])
            if not product_id:
                raise UserError("NO SE ENCUENTRA EL PRODUCTO CON REF %s"
                                % values['product_code'])

            # stock_line = self.env['stock.inventory.line'].search([
            #     ('inventory_id', '=', inventory_obj.id),
            #     ('product_id', '=', product_id.id),
            #     ('location_id', '=', location_obj.id),
            # ])

            # if stock_line:
            #     _logger.info("Updating stock line for %s" %
            #                  values['product_code'])
            #     stock_line.product_qty += float(values['product_qty'])
            # else:

            line_values = {
                'product_id': product_id.id,
                'location_id': location_obj.id,
                'product_qty': values['product_qty'],
                'inventory_id': inventory_obj.id,
                'product_uom_id': product_id.uom_id.id,
            }
            if values['product_lot_id']:
                product_lot_obj = self.env['stock.production.lot'].search([
                    ('name', '=', values['product_lot_id']),
                    ('product_id', '=', product_id.id),
                ])
                if not product_lot_obj:
                    product_lot_obj = self.env['stock.production.lot'].create({
                        'name': values['product_lot_id'],
                        'product_id': product_id.id,
                        'company_id': self.env.user.company_id.id,
                    })
                line_values.update({'prod_lot_id': product_lot_obj.id})

            stock_line = self.env['stock.inventory.line'].create(line_values)
        return stock_line

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
            if temp == '\ufeff"location_id"':
                temp = 'location_id'
            keys.append(temp)

        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            if reader_info[i]:
                field = reader_info[i]
                values = dict(zip(keys, field))
                self.with_delay().\
                    _create_new_stock_inventory(values)
        return {'type': 'ir.actions.act_window_close'}
