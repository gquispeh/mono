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


class ImportProductCategory(models.TransientModel):
    _name = "import.product.category"
    _description = "Import Product Category"

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter ","',
    )

    def _create_product_category(self, values):
        product_category_obj = self.env['product.category']
        category_vals = {}

        product_category_obj = product_category_obj.search([(
            'complete_name', '=', values['complete_name'])])

        if product_category_obj:
            # GET LOGISTICS COST
            if values.get('logistics_cost', False):
                values['logistics_cost'] = float(
                    values['logistics_cost'].replace(',', '.'))
                category_vals.update({
                    'estimate_cost': values['logistics_cost']
                })

            # SEARCH INTRASTAT
            if values.get('arancel_id', False):
                values['arancel_id'] = values['arancel_id'].zfill(8)
                intrastat_obj = self.env['account.intrastat.code'].search([(
                    'code', '=', values['arancel_id'])])
                if intrastat_obj:
                    category_vals.update({
                        'intrastat_id': intrastat_obj.id,
                    })

            # SEARCH PM / FAES
            if values.get("pms", False):
                if values['pms']:
                    pm_ids = []
                    for name in values['pms'].split(';'):
                        if name != '':
                            pm = self.env['res.users'].with_context(
                                active_test=False).search([(
                                    'name', '=', name)])
                            if pm:
                                pm_ids.append(pm.id)
                    category_vals.update({
                        'product_manager': [(6, 0, pm_ids)]
                    })
            if values.get("faes", False):
                if values['faes']:
                    fae_ids = []
                    for name in values['faes'].split(';'):
                        if name != '':
                            fae = self.env['res.users'].with_context(
                                active_test=False).search([(
                                    'name', '=', name)])
                            if fae:
                                fae_ids.append(fae.id)
                    category_vals.update({
                        'field_application_engineer': [(6, 0, fae_ids)]
                    })

            product_category_obj.write(category_vals)
            _logger.info(
                "Updated Product Category: %s",
                product_category_obj.complete_name)

        else:
            if values['parent_id']:
                domain = [('complete_name', '=', values['parent_id'])]
                parent_obj = self.env['product.category'].search(domain)
                parent_id = parent_obj.id
            else:
                parent_id = False

            category_vals.update({
                'name': values['name'],
                'parent_id': parent_id,
            })

            # GET LOGISTICS COST
            if values.get('logistics_cost', False):
                values['logistics_cost'] = float(
                    values['logistics_cost'].replace(',', '.'))
                category_vals.update({
                    'estimate_cost': values['logistics_cost']
                })

            # SEARCH INTRASTAT
            if values.get('arancel_id', False):
                values['arancel_id'] = values['arancel_id'].zfill(8)
                intrastat_obj = self.env['account.intrastat.code'].search([(
                    'code', '=', values['arancel_id'])])
                if intrastat_obj:
                    category_vals.update({
                        'intrastat_id': intrastat_obj.id,
                    })

            # SEARCH PM / FAES
            if values.get("pms", False):
                if values['pms']:
                    pm_ids = []
                    for name in values['pms'].split(';'):
                        if name != '':
                            pm = self.env['res.users'].with_context(
                                active_test=False).search([(
                                    'name', '=', name)])
                            if pm:
                                pm_ids.append(pm.id)
                    category_vals.update({
                        'product_manager': [(6, 0, pm_ids)]
                    })
            if values.get("faes", False):
                if values['faes']:
                    fae_ids = []
                    for name in values['faes'].split(';'):
                        if name != '':
                            fae = self.env['res.users'].with_context(
                                active_test=False).search([(
                                    'name', '=', name)])
                            if fae:
                                fae_ids.append(fae.id)
                    category_vals.update({
                        'field_application_engineer': [(6, 0, fae_ids)]
                    })

            product_category_obj = product_category_obj.create(category_vals)

            _logger.info(
                "Created Product Category: %s",
                product_category_obj.complete_name)

        return product_category_obj

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
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self._create_product_category(values)

        return {'type': 'ir.actions.act_window_close'}
