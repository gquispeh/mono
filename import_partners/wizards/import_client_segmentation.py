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


class ImportClientSegmentation(models.TransientModel):
    _name = "import.client.segmentation"
    _description = "Import Client Segmentation"

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter ","',
    )

    def _create_client_segmentation(self, values):
        client_segmentation_obj = self.env['monolitic.client.segmentation']
        if values['parent_id']:
            domain = [('complete_name', '=', values['parent_id'])]
            parent_obj = self.env[
                'monolitic.client.segmentation'].search(domain)
            parent_id = parent_obj.id
        else:
            parent_id = False

        client_segmentation_obj = client_segmentation_obj.create({
            'name': values['name'],
            'parent_id': parent_id,
        })

        _logger.info('LINEA: %s', values['name'])
        _logger.info(
            "Created Client Segmentation: %s",
            client_segmentation_obj.complete_name)
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
            # Don't read rows that start with ( , ' ' or are empty
            if reader_info[i]:
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self._create_client_segmentation(values)

        return {'type': 'ir.actions.act_window_close'}
