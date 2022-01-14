# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _

import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportChartAccount(models.TransientModel):
    _name = 'import.chart.account'
    _description = 'Import Chart Account'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default=',',
        help='Default delimiter ","',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True
    )

    '''
        Function to create or update the chart account.

        :param values: Dict with the values to import.
    '''
    def _create_or_update_chart_account(self, values):
        if not values['code'][:3] in ('400', '410', '430'):
            first = False
            if len(values['code']) < 6:
                values['code'] = values['code'].ljust(6, '0')
            else:
                max_len = len(values['code'])
                for digit in range(0, max_len):
                    if values['code'][digit] == '0':
                        if first:
                            last = 6 - first
                            new_code = values['code'][:digit-1] + \
                                values['code'][-last:]
                            values['code'] = new_code
                            break
                        first = digit
                    else:
                        first = False
            chart_acc_obj = self.env['account.account'].search([
                ('code', '=', values['code']),
                ('company_id', '=', self.company_id.id)])

            if not chart_acc_obj:
                group_acc = False
                for digit in reversed(range(0, 6)):
                    parent_code = values['code'][:digit].ljust(6, '0')
                    parent_account = self.env['account.account'].search([
                        ('code', '=', parent_code),
                        ('company_id', '=', self.company_id.id),
                    ])
                    if parent_account and not chart_acc_obj:
                        values = {
                            'code': values['code'],
                            'name': values['name'],
                            'user_type_id': parent_account.user_type_id.id,
                            'company_id': self.company_id.id,
                            'reconcile': parent_account.reconcile,
                        }
                        _logger.info(
                            'Creating chart of account %s', values['code']
                        )
                        chart_acc_obj = chart_acc_obj.create(values)
                    if not group_acc:
                        group_acc = self.env['account.group'].search([
                            ('code_prefix_start', '<=', values[
                                'code'][:digit]),
                            ('code_prefix_end', '>=', values[
                                'code'][:digit]),
                            ('company_id', '=', self.company_id.id)
                        ])
                if group_acc:
                    chart_acc_obj.write({
                        'group_id': group_acc.id,
                    })
            else:
                group_acc = False
                for digit in reversed(range(0, 6)):
                    if not group_acc:
                        group_acc = self.env['account.group'].search([
                            ('code_prefix_start', '<=', values[
                                'code'][:digit]),
                            ('code_prefix_end', '>=', values[
                                'code'][:digit]),
                            ('company_id', '=', self.company_id.id)
                        ])

                if group_acc:
                    chart_acc_obj.write({
                        'group_id': group_acc.id,
                    })

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
            keys.append(temp)

        del reader_info[0]
        values = {}

        for i in range(len(reader_info)):
            # Don't read rows that start with ( , ' ' or are empty
            if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                self._create_or_update_chart_account(values)

        return {'type': 'ir.actions.act_window_close'}
