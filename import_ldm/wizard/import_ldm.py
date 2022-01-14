# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2019 Roger Escola <roger.escola@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _
from datetime import datetime
from odoo.exceptions import UserError

import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportMrpBom(models.Model):
    _name = 'import.ldm'
    _description = 'Import LdM'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )

    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _assign_product_data(self, values):
        if values['code']:
            product_tmpl = self.env['product.template'].with_context(
                    active_test=False).search([(
                        'default_code', '=', values['product_tmpl'])])
            if product_tmpl:
                values.update({
                    'product_tmpl': product_tmpl[0].id,
                })
            else:
                values.update({
                    'product_tmpl': False,
                })

        # Search for the component product
        if values['product_comp']:
            product_comp = self.env['product.product'].with_context(
                    active_test=False).search([(
                        'default_code', '=', values['product_comp'])])
            if product_comp:
                values.update({
                    'product_comp': product_comp[0].id,
                    'product_uom_id': product_comp.uom_id.id,
                })
            else:
                values.update({
                    'product_comp': False,
                })
        return values

    '''
        Function to create the mrp nom.
        Creation of  phanotm BOMS

        :param values: Dict with the values to import.
    '''
    def _create_new_ldm(self, values):
        updated_values = self._assign_product_data(values)
        if not updated_values['product_tmpl']:
            raise UserError(
                "Producto de LdM no encontrado %s" % values['product_tmpl'])

        if not updated_values['product_comp']:
            raise UserError(
                "Producto Componente no encontrado %s" % values['product_comp'])

        ldm_obj = self.env['mrp.bom'].search([
            ('code', '=', values['code']),
            ('product_tmpl_id', '=', updated_values['product_tmpl'])
        ])

        line_values = {
            'product_id': updated_values['product_comp'],
            'product_qty': float(updated_values['comp_qty'].replace(',','.')),
        }

        if ldm_obj:
            ldm_obj.write({
                'type': values['type'],
                'product_uom_id': updated_values.get('product_uom_id'),
                'bom_line_ids': [(0, 0, line_values)]
            })
            _logger.info(
                "Adding component line for LDM: %s", values['code'])
        else:
            ldm_obj = ldm_obj.create({
                'code': values['code'],
                'product_tmpl_id': updated_values['product_tmpl'],
                'product_qty': updated_values['product_qty'],
                'type': values['type'],
                'bom_line_ids': [(0, 0, line_values)]
            })
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
                    UPDATE mrp_bom
                    SET create_date = %s, create_uid = %s
                    WHERE id = %s
                """, (values['create_date'], user_obj.id, str(ldm_obj.id)))
                created_message = self.env['mail.message'].sudo().search([
                    ('res_id', '=', ldm_obj.id),
                    ('model', '=', 'mrp.bom'),
                ], order='id asc', limit=1)
                if created_message:
                    self._cr.execute("""
                        UPDATE mail_message
                        SET date = %s, author_id = %s
                        WHERE id = %s
                    """, (values['create_date'], user_obj.partner_id.id, str(created_message.id)))
            _logger.info(
                "Creating component line for LDM: %s", values['code'])
        return ldm_obj

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
        ldm = []
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
            if temp == '\ufeff"code"':
                temp = 'code'
            keys.append(temp)

        del reader_info[0]
        values = {}

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay()._create_new_ldm(values)

        return {'type': 'ir.actions.act_window_close'}

    # def action_update_uom(self):
    #     bom = self.env['mrp.bom'].search([])
    #     for l in bom:
    #         variant = self.env['product.product'].search([(
    #             'product_tmpl_id', '=', l.product_tmpl_id.id)])
    #         if variant:
    #             if variant.uom_id.id != l.product_uom_id.id:
    #                 _logger.info('ACTUALIZA UOM')
    #                 l.product_uom_id = variant.uom_id.id
