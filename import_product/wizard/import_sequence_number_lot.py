from odoo import fields, models, exceptions, _
from datetime import datetime

import base64
import csv
from io import StringIO


class ImportSequenceNumberLot(models.TransientModel):
    _name = 'import.sequence.number.lot'
    _description = 'Import Sequence Number Lot'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default=';',
        help='Default delimiter ";"',
    )

    def _create_new_sequence_lot(self, values):
        values['company_id'] = 1
        if values['product_id']:
            product_obj = self.env['product.product'].search(
                [('default_code','=', values['product_id'])]
            )
            if product_obj:
                values['product_id'] = product_obj.id
            else:
                return

        lot_obj = self.env['stock.production.lot'].search(
            [('name', '=', values['name']),('product_id','=',product_obj.id)]
        )

        if lot_obj:
            lot_obj.write(values)
        else:
            lot_obj = self.env['stock.production.lot'].create(values)

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
            keys.append(temp)
        del reader_info[0]

        values = {}

        for i in range(len(reader_info)):
            # Don't read rows that start with ( or are empty
            if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                #self.with_delay()._create_new_sequence_lot(values, self.update)
                self._create_new_sequence_lot(values)

        return {'type': 'ir.actions.act_window_close'}
