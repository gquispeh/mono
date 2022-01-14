# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, exceptions, _
from odoo.tools import formataddr
import base64
import csv
from io import StringIO
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


MODEL_FIELD_MAPPER = {
    'res.partner': 'ref',
    'account.invoice': 'number',
    'crm.lead': 'code',
    'product.template': 'default_code',
    'sale.order': 'name',
    'stock.picking': 'name',
    'mrp.production': 'name',
    'crm.claim.ept': 'code',
    'claim.line.ept': 'unique_code',
}


class ImportMessage(models.Model):
    _name = 'import.message'
    _description = "model for import messages"

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

    def _check_already_exists(self, vals=False):
        try:
            rec = self.env['mail.message'].search([
                ('unique_code', '=', vals['unique_code']),
            ])
            if rec:
                return rec

            return False

        except Exception:
            return False

    def _prepare_message(self, vals):
        ICP = self.env['ir.config_parameter'].sudo()
        catchall_alias = ICP.get_param("mail.catchall.alias")
        catchall_domain = ICP.get_param("mail.catchall.domain")
        note_subtype = self.env.ref('mail.mt_note')

        vals['res_model'] = vals['res_model'].replace('_', '.')

        domain = (
            MODEL_FIELD_MAPPER[vals['res_model']], '=', vals['res_id']
        )
        res_obj = self.env[vals['res_model']].with_context(
            active_test=False).search([domain])
        if res_obj:
            body = vals['body']
            body_formatted = '<p>' + body.replace('\n', '<br>') + '</p>'

            res = {
                'unique_code': vals['unique_code'],
                'subject': vals['subject'],
                'date': vals['date'],
                'message_type': 'comment',
                'subtype_id': note_subtype.id,
                'res_id':  res_obj.id,
                'model': vals['res_model'],
                'reply_to': '%s@%s' % (catchall_alias, catchall_domain),
                'body': body_formatted,
            }
            if vals['id_attachment']:
                attach_obj = self.env['ir.attachment'].search([
                    ('unique_code', '=', vals['id_attachment'])])
                if attach_obj:
                    res.update({
                        'attachment_ids': [(6, 0, [attach_obj.id])]
                    })
                else:
                    raise UserError("Adjunto no encontrado %s" % vals['id_attachment'])

            user_obj = self.env[
                'res.users'].with_context(active_test=False).search([
                    ('name', '=', vals['author_id'])])
            if user_obj:
                res.update({
                    'author_id': user_obj.partner_id.id,
                    'email_from': formataddr((
                        user_obj.partner_id.name,
                        user_obj.partner_id.email
                    ))
                })

            return res
        else:
            raise UserError("Error buscando el documento origen %s" % vals['res_id'])

    def _create_message(self, vals):
        message_vals = self._prepare_message(vals)
        if not message_vals:
            return False

        msg_obj = self._check_already_exists(message_vals)
        if msg_obj:
            msg_obj.write(message_vals)
            return "Message %s updated." % msg_obj.unique_code

        msg_obj = self.env['mail.message'].create(message_vals)
        return 'Message %s imported.' % msg_obj.unique_code

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
        list_vals = []

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    list_vals.append(dict(zip(keys, field)))
        return list_vals

    def action_import(self):
        """Load Inventory data from the CSV file."""
        rows_data = self._format_file(self.data)
        for row in rows_data:
            self.with_delay()._create_message(row)

        return {'type': 'ir.actions.act_window_close'}
