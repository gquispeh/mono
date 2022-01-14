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


class UpdateStockDates(models.Model):
    _name = 'update.stock.dates'
    _description = 'Update Stock Dates'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )

    '''
        Function to create the mrp nom.

        :param values: Dict with the values to import.
    '''
    def _update_stock_dates(self, values,):
        if values['date']:
            if not values['product_code']:
                _logger.info("En una linea falta el product_code")
            if values['product_code']:
                location_obj = self.env['stock.location'].search([(
                    'complete_name', '=', values['location_id'])])
                if not location_obj:
                    _logger.info(
                        "No se encuentra la ubicación %s" % values['location_id'])

                # Search for line
                product_id = self.env['product.product'].search([
                    ('default_code', '=', values['product_code'])
                ])
                if not product_id:
                    _logger.info("NO SE ENCUENTRA EL PRODUCTO CON REF %s" % values['product_code'])

                if values['product_lot_id']:
                    lot_id = self.env['stock.production.lot'].search([
                        ('product_id', '=', product_id.id),
                        ('name', '=', values['product_lot_id']),
                    ], limit=1)
                    if lot_id:
                        lot_id = lot_id.id
                    else:
                        lot_id = False
                else:
                    lot_id = False

                if values['product_qty']:
                    values['product_qty'] = values[
                        'product_qty'].replace('.', '')
                    values['product_qty'] = values[
                        'product_qty'].replace(',', '.')

                _logger.info('PRODUCTO: %s' % values['product_code'])
                _logger.info(product_id)

                # Search for quant
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', product_id.id),
                    ('location_id', '=', location_obj.id),
                    ('lot_id', '=', lot_id),
                ], limit=1)
                if quant:
                    self.sudo()._cr.execute("""
                        UPDATE stock_quant
                        SET in_date = %s
                        WHERE id = %s
                    """, (values['date'], str(quant.id)))

                    _logger.info('ACTUALIZANDO QUANT')

                # Search for move lines
                move = self.env['stock.move.line'].search([
                    ('product_id', '=', product_id.id),
                    ('location_dest_id', '=', location_obj.id),
                    ('lot_id', '=', lot_id),
                    ('reference', 'ilike', 'INV'),
                ], limit=1)
                if move:
                    self.sudo()._cr.execute("""
                        UPDATE stock_move
                        SET date = %s
                        WHERE id = %s
                    """, (values['date'], str(move.id)))

                    _logger.info('ACTUALIZANDO MOVE')

                # Search for move lines
                move_line = self.env['stock.move.line'].search([
                    ('move_id', '=', move.id),
                ], limit=1)
                if move_line:
                    self.sudo()._cr.execute("""
                        UPDATE stock_move_line
                        SET date = %s
                        WHERE id = %s
                    """, (values['date'], str(move_line.id)))

                    _logger.info('ACTUALIZANDO MOVE LINE')

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
                self._update_stock_dates(values)
        return {'type': 'ir.actions.act_window_close'}
