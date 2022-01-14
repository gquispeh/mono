# Copyright 2021 Daniel López <daniel.lopez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, exceptions, _
import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportCommercialTarget(models.Model):
    _name = 'import.commercial.target'
    _description = 'Import commercial target wizard'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default=';',
        help='Default delimiter ","',
    )

    def _assign_target_data(self, values):
        target_data = {}

        # Assign total_amount
        if values['total_amount']:
            values['total_amount'] = values['total_amount'].replace('.', '')
            values['total_amount'] = values['total_amount'].replace(',', '.')
            target_data.update({
                'total_amount': values['total_amount']
            })
        del values['total_amount']

        # Assign commercial
        if values['commercial']:
            commercial_obj = self.env['res.users'].search([
                ('name', '=', values['commercial'])])
            if commercial_obj:
                target_data.update({
                    'related_user': commercial_obj.id,
                    'user_id': commercial_obj.id
                })
        del values['commercial']

        # Assign market_seg
        if values['market_segmentation']:
            market_seg_obj = self.env['monolitic.client.segmentation'].search(
                [("complete_name", "=", values['market_segmentation'])])
            if market_seg_obj:
                target_data.update({
                    'market_segmentation_id': market_seg_obj.id
                })

        # Assign product_seg
        if values['product_segmentation']:
            product_cat_obj = self.env['product.category'].search(
                [("complete_name", "=", values['product_segmentation'])])
            if product_cat_obj:
                target_data.update({
                    'product_segmentation_id': product_cat_obj.id
                })

        del values['market_segmentation']
        del values['product_segmentation']

        return target_data

    def _create_new_target(self, values):
        logging.info(values)
        target_obj = self.env['commercial.target']
        fields = self._assign_target_data(values)

        target_obj = target_obj.sudo().create(fields)
        target_obj._onchange_total_amount()

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
                self.with_delay()._create_new_target(values)

        return {'type': 'ir.actions.act_window_close'}
