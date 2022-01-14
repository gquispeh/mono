from odoo import fields, models, exceptions, _
from odoo.exceptions import UserError

import base64
import csv
from io import StringIO


class ImportMrpBomOperations(models.Model):
    _name = 'import.ldm.operations'
    _description = 'Import LdM Operations'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )

    def _create_new_operation(self, values):
        ldm_obj = self.env['mrp.bom'].search([(
            'product_tmpl_id', '=', values['product_id'])])
        if not ldm_obj:
            raise UserError(
                "LdM no encontrada %s" % values['product_id'])
        del values['product_id']

        if values['workcenter_id']:
            workcenter = self.env['mrp.workcenter'].search([(
                'name', '=', values['workcenter_id'])])
            if not workcenter:
                workcenter = self.env['mrp.workcenter'].create({
                    'name': values['workcenter_id'],
                    'resource_calendar_id': 1
                })
            values.update({
                    'workcenter_id': workcenter.id,
            })

        if values['time_cycle_manual']:
            values['time_cycle_manual'] = float(
                values['time_cycle_manual'].replace(',', '.')) * 60

        operation = self.env['mrp.routing.workcenter'].search([
            ('name', '=', values['name']),
            ('time_cycle_manual', '=', values['time_cycle_manual'])
        ])

        if not operation:
            operation = self.env['mrp.routing.workcenter'].create(values)

        if ldm_obj:
            ldm_obj.write({
                'operation_ids': [(4, operation.id)]
            })

        return operation

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
            if temp == '\ufeff"product_id"':
                temp = 'product_id'
            keys.append(temp)
        del reader_info[0]

        values = {}

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay()._create_new_operation(values)

        return {'type': 'ir.actions.act_window_close'}
