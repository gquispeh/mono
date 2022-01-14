# Copyright 2020 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, exceptions, _
from odoo.exceptions import UserError

import base64
import csv
import datetime
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportRma(models.TransientModel):
    _name = 'import.rma'
    _description = 'Import RMA'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimiter', default='|',
                            help='Default delimiter "|"')
    import_type = fields.Selection(
        string='Type',
        selection=[('crm.claim.ept', 'RMA Order'),
                   ('claim.line.ept', 'RMA Order Line'),
                   ('ml.notes.rma', 'RMA Order Line Notes')],
        default="crm.claim.ept")


    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _assign_rma_values(self,values):
        # User
        if values['user_id']:
            user_obj = self.env['res.users'].search([('name','=',values['user_id'])])
            if user_obj:
                values['user_id'] = user_obj.id
            else:
                raise UserError(_(
                    "User %s does not exist."
                ) % values['user_id'])
        # Section
        if values['section_id']:
            section_obj = self.env['crm.team'].search([('name','=',values['section_id'])])
            if section_obj:
                values['section_id'] = section_obj.id
            else:
                raise UserError(_(
                    "Section %s does not exist."
                ) % values['section_id'])
        # RMA support person
        if values['rma_support_person_id']:
            support_person_obj = self.env['res.partner'].search([('name','=',values['rma_support_person_id'])])
            if support_person_obj:
                values['rma_support_person_id'] = support_person_obj.id
            else:
                raise UserError(_(
                    "RMA support person %s does not exist."
                ) % values['rma_support_person_id'])
        # Picking
        if values['picking_id']:
            picking_obj = self.env['stock.picking'].search([('name','=',values['picking_id'])])
            if picking_obj:
                values['picking_id'] = picking_obj.id
            else:
                raise UserError(_(
                    "Picking %s does not exist."
                ) % values['picking_id'])
        # Partner
        if values['partner_id']:
            partner_obj = self.env['res.partner'].search([('name','=',values['partner_id'])])
            if partner_obj:
                values['partner_id'] = partner_obj[0].id
            else:
                raise UserError(_(
                    "Partner %s does not exist."
                ) % values['partner_id'])
        # Location
        if values['location_id']:
            location_obj = self.env['stock.location'].search([('name','=',values['location_id'])])
            if location_obj:
                values['location_id'] = location_obj.id
            else:
                raise UserError(_(
                    "Location %s does not exist."
                ) % values['location_id'])
        # Partner delivery
        if values['partner_delivery_id']:
            partner_delivery_obj = self.env['res.partner'].search([('name','=',values['partner_delivery_id'])])
            if partner_delivery_obj:
                values['partner_delivery_id'] = partner_delivery_obj[0].id
            else:
                raise UserError(_(
                    "Partner delivery %s does not exist."
                ) % values['partner_delivery_id'])


        return values

    def _create_rma(self, values):
        _logger.info(values)
        fields = self._assign_rma_values(values)
        rma_obj = self.env['crm.claim.ept']
        if values['code']:
            rma_obj.search([('code','=',values['code'])])
        del values['code']

        if rma_obj:
            rma_obj.sudo().write(fields)
        else:
            rma_obj = self.env['crm.claim.ept'].sudo().create(fields)

    def _assign_rma_line_values(self,values):
        #Product
        if values['product_id']:
            product_obj = self.env['product.template'].search([('name','=',values['product_id'])])
            if product_obj:
                values['product_id'] = product_obj[0].id
            else:
                raise UserError(_(
                    "Product: %s does not exist."
                ) % values['product_id'])
        #Product category
        if values['product_categ_id']:
            product_categ_obj = self.env['product.category'].search([('complete_name','=',values['product_categ_id'])])
            if product_categ_obj:
                values['product_categ_id'] = product_categ_obj.id
            else:
                raise UserError(_(
                    "Product category: %s does not exist."
                ) % values['product_categ_id'])
        #Product manufacturer
        if values['product_manufacturer']:
            manufacturer_obj = self.env['res.partner'].search([('name','=',values['product_manufacturer'])])
            if manufacturer_obj:
                values['product_manufacturer'] = manufacturer_obj.id
            else:
                raise UserError(_(
                    "Product manufacturer: %s does not exist."
                ) % values['product_manufacturer'])
        #Reason
        if values['rma_reason_id']:
            reason_obj = self.env['rma.reason.ept'].search([('name','=',values['rma_reason_id'])])
            if reason_obj:
                values['rma_reason_id'] = reason_obj.id
            else:
                raise UserError(_(
                    "Reason: %s does not exist."
                ) % values['rma_reason_id'])
        #State
        if values['ept_state_id']:
            state_obj = self.env['crm.claim.ept.state'].search([('name','=',values['ept_state_id'])])
            if state_obj:
                values['ept_state_id'] = state_obj.id
            else:
                raise UserError(_(
                    "State: %s does not exist."
                ) % values['ept_state_id'])

        return values

    def _create_rma_line(self, values):
        _logger.info(values)
        fields = self._assign_rma_line_values(values)
        rma_obj = self.env['crm.claim.ept'].search([('code','=',values['code'])])
        if not rma_obj:
            raise UserError(_(
                    "RMA: %s does not exist."
                ) % values['code'])
        del values['code']
        rma_line = self.env['claim.line.ept'].create(fields)
        if rma_line:
            rma_obj.sudo().write({'claim_line_ids': [(6,0,rma_line.id)]})

    def _create_rma_line_notes(self,values):
        rma_obj = self.env['crm.claim.ept'].search([('code','=',values['code'])])
        if not rma_obj:
            raise UserError(_(
                    "RMA: %s does not exist."
                ) % values['code'])
        product = self.env['product.product'].search([('name','=',values['product_id'])])
        if not product:
            raise UserError(_(
                    "Product: %s does not exist."
                ) % values['product_id'])
        rma_line_obj = rma_obj.claim_line_ids.search([('product_id','=',product[0].id)])
        if not rma_line_obj:
            raise UserError(_(
                    "RMA line with product: " + values['product_id'] + " not exists in " + values['code']
                ))
        del values['code']
        del values['product_id']
        values['res_id'] = rma_line_obj.id
        self.env['ml.notes.rma'].create(values)
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
            if temp == '\ufeff"code"':
                temp = 'code'
            keys.append(temp)
        del reader_info[0]
        _logger.info('The keys of the file are: ')
        _logger.info(keys)

        values = {}

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    if self.import_type == "crm.claim.ept":
                        # self.with_delay()._create_rma(values)
                        self._create_rma(values)
                    elif self.import_type == "claim.line.ept":
                        # self.with_delay()._create_rma_line(values)
                        self._create_rma_line(values)
                    else:
                        # self.with_delay()._create_rma_line_notes(values)
                        self._create_rma_line_notes(values)

        return {'type': 'ir.actions.act_window_close'}
