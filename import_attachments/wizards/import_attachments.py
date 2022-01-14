# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, exceptions, _
import base64
import csv
from io import StringIO
import os
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

MODEL_FIELD_MAPPER = {
    'res.partner': 'ref',
    'crm.lead': 'code',
    'product.template': 'default_code',
    'sale.order': 'name',
    'stock.picking': 'name',
    'mrp.production': 'name',
    'crm.claim.ept': 'code',
    'claim.line.ept': 'unique_code',
}


class ImportAttachements(models.TransientModel):
    _name = 'import.attachments'
    _description = "model for import attachments"

    name = fields.Char(string='Filename')
    data = fields.Binary(string='File', required=True)
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )
    update = fields.Boolean()

    def _find_files(self, filename, search_path):
        for root, dir, files in os.walk(search_path):
            if filename in files:
                return os.path.join(root, filename)

    def _encoding_file(self, file_dir):
        with open(file_dir, 'rb') as f:
            return base64.b64encode(f.read())

    def _get_attributes(self, values, keyword, id):
        for row in values:
            for k, v in row.items():
                if k == 'id' and int(id) != int(v):
                    break
                if k == keyword:
                    return k, v
        return False

    def _get_domain(self, model, id):
        pass

    # This Function Get The ID for the record related
    def _get_record_related(self, model, id=False, old_id=False):
        if old_id:
            try:
                rec_id = self.env[model].search([
                    ('old_id', '=', old_id)
                ]).id
            except Exception:
                # Way to create fields to one model
                pass

            if not rec_id:
                if self._update_old_id(model, old_id):
                    return self._get_record_related(
                        model, id, old_id
                    )
                else:

                    return False
            else:
                return rec_id
        else:
            return id

    def _check_already_exists(self, values=False):
        rec = self.env['ir.attachment'].search([
            ('unique_code', '=', values['unique_code']),
        ])
        if rec:
            return rec

        return False

    def _prepare_attachment(self, values):
        file_path = self._find_files(values['name'], values['path'])
        values['res_model'] = values['res_model'].replace('_', '.')
        if file_path:
            domain = (
                MODEL_FIELD_MAPPER[values['res_model']], '=', values['res_id']
            )
            res_obj = self.env[values['res_model']].with_context(
                active_test=False).search([domain])
            if res_obj:
                res = {
                    'unique_code': values['unique_code'],
                    'name': values['name'],
                    'datas': self._encoding_file(file_path),
                    'type': 'binary',
                    'res_id': res_obj.id,
                    'res_model': values['res_model'],
                    'description': values['comments'],
                }

                return res
            else:
                raise UserError("Error buscando el documento origen %s" % values['res_id'])
        else:
            raise UserError('File not found!')

    def _create_attachment(self, values):
        attach_vals = self._prepare_attachment(values)
        if not attach_vals:
            return False

        attach_id = self._check_already_exists(attach_vals)
        if attach_id:
            attach_id.write(attach_vals)
            attach_id._inverse_datas()
            return 'Attachment %s updated.' % attach_id.name

        attach_id = self.env['ir.attachment'].create(attach_vals)
        attach_id._inverse_datas()
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
                UPDATE ir_attachment
                SET create_date = %s, create_uid = %s
                WHERE id = %s
            """, (values['create_date'], user_obj.id, str(attach_id.id)))

        return 'Attachment %s imported.' % attach_id.name

    def _format_file(self, file_data):
        if not file_data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(file_data).decode('utf-8')
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
        # Get column names
        keys = []
        for k in reader_info[0]:
            temp = k.replace(' ', '_')
            if temp == '\ufeff"unique_code"':
                temp = 'unique_code'
            keys.append(temp)

        del reader_info[0]
        list_values = []

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    list_values.append(dict(zip(keys, field)))
        return list_values

    def action_import(self):
        """Load Inventory data from the CSV file."""
        rows_data = self._format_file(self.data)
        for row in rows_data:
            self.with_delay()._create_attachment(row)
        return {'type': 'ir.actions.act_window_close'}
