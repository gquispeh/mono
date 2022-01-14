# Copyright 2021 Daniel López <daniel.lopez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _
from odoo.exceptions import UserError
import base64
import csv
import datetime
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportCustomerPrevision(models.Model):
    _name = 'import.customer.prevision'
    _description = 'Import commercial target wizard'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter "|"',
    )

    def _assign_prevision_data(self, values):
        if values['ref']:
            partner_obj = self.env['res.partner'].with_context(
                active_test=False).search([('ref', '=', values['ref'])])
            if partner_obj:
                values.update({
                    'partner_id': partner_obj.id
                })
            else:
                raise UserError(_("Invalid client ref: " + values['ref']))
        del values['ref']

        if values['commercial']:
            commercial_obj = self.env['res.users'].with_context(
                active_test=False).search([(
                    'name', '=', values['commercial'])])
            if commercial_obj:
                values.update({
                    'user_id': commercial_obj.id
                })
            else:
                raise UserError(_(
                    "Invalid commercial id: " + values['commercial']))
        del values['commercial']

        if values['market_segmentation']:
            market_seg_obj = self.env['monolitic.client.segmentation'].search(
                [("complete_name", "=", values['market_segmentation'])])
            if market_seg_obj:
                values.update({
                    'market_segmentation_id': market_seg_obj.id
                })
            else:
                raise UserError(_(
                    "Invalid market segmentation id: " + values[
                        'market_segmentation']))
        del values['market_segmentation']
        if values['product_segmentation']:
            product_cat_obj = self.env['product.category'].search(
                [("complete_name", "=", values['product_segmentation'])])
            if product_cat_obj:
                values.update({
                    'product_segmentation_id': product_cat_obj.id
                })
            else:
                raise UserError(_(
                    "Invalid product segmentation id: " + values[
                        'product_segmentation']))
        del values['product_segmentation']
        if values['total_amount']:
            values['total_amount'] = values['total_amount'].replace('.', '')
            values['total_amount'] = values['total_amount'].replace(',', '.')
            values.update({
                'total_amount': values['total_amount']
            })

        return values

    def _create_customer_prevision(self, values):
        logging.info(values)
        prevision_obj = self.env['customer.prevision']
        current_oppn = self.env['crm.lead']
        oppn_code = values['oppn']
        del values['oppn']
        fields = self._assign_prevision_data(values)
        if oppn_code:
            current_oppn = current_oppn.search([(
                'code', '=', oppn_code)])
        else:
            current_oppn = current_oppn.search([
                ('name', '=', 'Previsión 2022'),
                ('partner_id', '=', fields['partner_id'])])
        if current_oppn:
            cust_prevision_obj = current_oppn.customer_prevision_ids.search([
                ('year', '=', fields['year']),
                ('user_id', '=', fields['user_id']),
                ('partner_id', '=', fields['partner_id']),
                ('lead_id', '=', current_oppn.id)])
            if cust_prevision_obj:
                cust_prevision_obj.write(fields)
                cust_prevision_obj._calculate_monthly_amounts()
            else:
                fields['lead_id'] = current_oppn.id
                prevision_obj = prevision_obj.sudo().create(fields)
        else:
            current_oppn = current_oppn.sudo().with_context(
                default_type='opportunity').create({
                    'name': "Previsión 2022",
                    'partner_id': fields['partner_id'],
                    'is_express': True,
                    'date_deadline': datetime.datetime(2022, 12, 31),
                    'type': 'opportunity'
                })
            fields['lead_id'] = current_oppn.id
            prevision_obj = prevision_obj.sudo().create(fields)

        prevision_obj._calculate_monthly_amounts()

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
            if temp == '\ufeff"year"':
                temp = 'year'
            keys.append(temp)
        _logger.info('The keys of the file are: ')
        _logger.info(keys)
        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay()._create_customer_prevision(values)
                    # self._create_customer_prevision(values)

        return {'type': 'ir.actions.act_window_close'}
