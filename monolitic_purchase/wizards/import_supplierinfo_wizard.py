# Copyright 2021 Albert Farrés <albert.farres@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, Warning
import base64
from io import StringIO
import logging
import csv
import binascii
import tempfile

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class ImportSupplierinfoWizard(models.TransientModel):
    _name = 'import.supplierinfo.wizard'
    _description = 'Import Supplierinfo from csv file'

    HEADER_LINE = 6
    SUPPLIER_COL = 0
    SUPPLIER_REF_COL = 1
    DEFAULT_CODE_COL = 2
    CURRENCY_ID_COL = 3
    DATE_START_COL = 4
    DATE_END_COL = 5
    DELAY_COL = 6

    supplierinfo_file = fields.Binary(string="Select File")

    def action_import_supplierinfo(self):
        if not self.supplierinfo_file:
            raise UserError("Please upload file first!")

        try:
            fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.supplierinfo_file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            reader_info = workbook.sheet_by_index(0)
        except Exception:
            raise Warning(_("Invalid file"))

        #Set top static values
        static_values = {
            'supplier_ref': str(int(float(reader_info.row(0)[2].value))) if reader_info.row(0)[2].ctype == 2 else str(reader_info.row(0)[2].value).upper(),
            'currency_id': str(reader_info.row(1)[2].value).upper(),
        }

        if reader_info.row(2)[2].ctype == 3:
            static_values.update({
                'date_start': xlrd.xldate.xldate_as_datetime(reader_info.row(2)[2].value, workbook.datemode),
            })
        elif reader_info.row(2)[2].value != '':
            static_values.update({
                'date_start':  datetime.strptime(reader_info.row(2)[2].value, '%d/%m/%Y'),
            })
        else:
            static_values.update({
                'date_start':  '',
            })

        if reader_info.row(3)[2].ctype == 3:
            static_values.update({
                'date_end': xlrd.xldate.xldate_as_datetime(reader_info.row(3)[2].value, workbook.datemode),
            })
        elif reader_info.row(3)[2].value != '':
            static_values.update({
                'date_end':  datetime.strptime(reader_info.row(3)[2].value, '%d/%m/%Y'),
            })
        else:
            static_values.update({
                'date_end':  '',
            })

        #Process every file line
        final_col = 0
        header = []
        header = list(map(lambda row: row.value, reader_info.row(self.HEADER_LINE)))
        final_col = header.index('Observaciones')
        empty_lines = 0

        for row_no in range(self.HEADER_LINE+1, reader_info.nrows):
            product_line = []
            product_line.append(str(int(float(reader_info.row(row_no)[self.SUPPLIER_COL].value))) if reader_info.row(row_no)[self.SUPPLIER_COL].ctype == 2 else str(reader_info.row(row_no)[self.SUPPLIER_COL].value))
            product_line.append(str(int(float(reader_info.row(row_no)[self.SUPPLIER_REF_COL].value))) if reader_info.row(row_no)[self.SUPPLIER_REF_COL].ctype == 2 else str(reader_info.row(row_no)[self.SUPPLIER_REF_COL].value))
            product_line.append(str(int(float(reader_info.row(row_no)[self.DEFAULT_CODE_COL].value))) if reader_info.row(row_no)[self.DEFAULT_CODE_COL].ctype == 2 else str(reader_info.row(row_no)[self.DEFAULT_CODE_COL].value))
            product_line.append(str(reader_info.row(row_no)[self.CURRENCY_ID_COL].value))

            if reader_info.row(row_no)[self.DATE_START_COL].ctype == 3:
                product_line.append(xlrd.xldate.xldate_as_datetime(reader_info.row(row_no)[self.DATE_START_COL].value, workbook.datemode))
            elif reader_info.row(row_no)[self.DATE_START_COL].value != '':
                product_line.append(datetime.strptime(reader_info.row(row_no)[self.DATE_START_COL].value, '%d/%m/%Y'))
            else:
                product_line.append('')

            if reader_info.row(row_no)[self.DATE_END_COL].ctype == 3:
                product_line.append(xlrd.xldate.xldate_as_datetime(reader_info.row(row_no)[self.DATE_END_COL].value, workbook.datemode))
            elif reader_info.row(row_no)[self.DATE_END_COL].value != '':
                product_line.append(datetime.strptime(reader_info.row(row_no)[self.DATE_END_COL].value, '%d/%m/%Y'))
            else:
                product_line.append('')

            product_line.append(str(reader_info.row(row_no)[self.DELAY_COL].value))

            for col_no in range(self.DELAY_COL+1,final_col+1):
                product_line.append(str(reader_info.row(row_no)[col_no].value))

            if any(field for field in product_line):
                self.process_supplierinfo_line(
                    product_line, static_values, header, final_col, workbook)
            else:
                empty_lines += 1
                if empty_lines >= 10:
                    return 0

        return 0

    def process_supplierinfo_line(self, line_data, static_data, header, final_col, workbook):
        # Check Supplier
        ref = ""
        if line_data[self.SUPPLIER_COL]:
            ref = line_data[self.SUPPLIER_COL].upper()
        else:
            if static_data['supplier_ref']:
                ref = static_data['supplier_ref']
            else:
                raise UserError("There's no Supplier on file!")
        supplier = self.env['res.partner'].with_context(
            active_test=False).search([
                ('ref', '=', ref), ('parent_id', '=', False)
            ])
        if not supplier:
            raise UserError("Supplier %s doesn't exist in Odoo!"
                            % ref)

        #Check Product
        if line_data[self.DEFAULT_CODE_COL]:
            product = self.env['product.template'].search([
                ('default_code', '=', line_data[self.DEFAULT_CODE_COL].upper())
            ])
            if product:
                if len(product) > 1:
                    raise UserError(
                                _("There are more than 1 product with the same odoo default"
                                  " code %s") % (line_data[self.DEFAULT_CODE_COL])
                            )
                else:
                    if line_data[self.SUPPLIER_REF_COL]:
                        if line_data[self.SUPPLIER_REF_COL] != product.supplier_internal_ref:
                            product.write({'supplier_internal_ref': line_data[self.SUPPLIER_REF_COL].upper()})
                            supplier_pricelists = self.env['product.supplierinfo'].search([
                                ('name', '=', supplier.id),
                                ('product_tmpl_id', '=', product.id),
                            ]).write({'product_code': line_data[self.SUPPLIER_REF_COL].upper()})
            else:
                if line_data[self.SUPPLIER_REF_COL]:
                    product = self.env['product.template'].search([
                        ('supplier_internal_ref', '=', line_data[self.SUPPLIER_REF_COL].upper())
                    ])
                    if product:
                        if len(product) > 1:
                            raise UserError(
                                _("There are more than 1 product with the same supplier internal"
                                  " reference %s") % (line_data[self.SUPPLIER_REF_COL])
                            )
                    if not product:
                        raise UserError(
                                _("There isn't any product with supplier internal"
                                  " reference %s") % (line_data[self.SUPPLIER_REF_COL])
                            )
        elif line_data[self.SUPPLIER_REF_COL]:
            product = self.env['product.template'].search([
                ('supplier_internal_ref', '=', line_data[self.SUPPLIER_REF_COL].upper())
            ])
            if product:
                if len(product) > 1:
                    raise UserError(
                        _("There are more than 1 product with the same supplier internal"
                            " reference %s") % (line_data[self.SUPPLIER_REF_COL])
                    )
            else:
                if not product:
                    raise UserError(
                            _("There isn't any product with supplier internal"
                                " reference %s") % (line_data[self.SUPPLIER_REF_COL])
                        )
        else:
            raise UserError("There's no supplier internal ref neither default code in this line!")

        # Check Currency
        currency = False
        if line_data[self.CURRENCY_ID_COL]:
            currency = self.env['res.currency'].search([
                ('name', '=', line_data[self.CURRENCY_ID_COL].upper())])
            if not currency:
                raise UserError("Currency %s doesn't exist in Odoo!" % line_data[self.CURRENCY_ID_COL])
        else:
            if static_data['currency_id']:
                currency = self.env['res.currency'].search([
                    ('name', '=', static_data['currency_id'])])
                if not currency:
                    raise UserError("Currency %s doesn't exist in Odoo!" % static_data['currency_id'])
            else:
                raise UserError("There is no currency in csv!")

        # Check Date Start
        date_start = False
        if line_data[self.DATE_START_COL]:
            date_start = line_data[self.DATE_START_COL].date()
        else:
            if static_data['date_start']:
                date_start = static_data['date_start'].date()

        # Check Date End
        date_end = False
        if line_data[self.DATE_END_COL]:
            date_end = line_data[self.DATE_END_COL].date()
        else:
            if static_data['date_end']:
                date_end = static_data['date_end'].date()
        if date_start and date_end:
            if date_start > date_end:
                raise UserError("End date %s must be after Start date %s!" % (date_end, date_start))

        # Loop for dynamic columns (min and max quantities)
        columns_without_data = 0
        for column in range(self.DELAY_COL+1, final_col):
            if line_data[column]:

                qty_values = self.get_min_max_qty(str(header[column]))

                supplierinfo = self.env['product.supplierinfo'].search([
                    ('name', '=', supplier.id),
                    ('product_tmpl_id', '=', product.id),
                    ('date_start', '=', date_start),
                    ('date_end', '=', date_end),
                    ('currency_id', '=', currency.id),
                    ('min_qty', '=', qty_values['min_qty']),
                    ('max_quantity', '=', qty_values['max_quantity']),
                ])

                final_values = {
                    'price': float(line_data[column].replace(',', '.')),
                }
                if line_data[self.DELAY_COL]:
                    final_values.update({
                        'delay': int(float(line_data[self.DELAY_COL])),
                    })
                if line_data[final_col]:
                    final_values.update({
                        'observations': line_data[final_col],
                    })

                # If the exact pricelist already exist, do nothing
                supplierinfo_already_exist = self.env['product.supplierinfo'].search([
                    ('name', '=', supplier.id),
                    ('product_tmpl_id', '=', product.id),
                    ('date_start', '=', date_start),
                    ('date_end', '=', date_end),
                    ('currency_id', '=', currency.id),
                    ('min_qty', '=', qty_values['min_qty']),
                    ('max_quantity', '=', qty_values['max_quantity']),
                    ('price', '=', line_data[column].replace(',','.')),
                    ('delay', '=', int(float(line_data[self.DELAY_COL])) if line_data[self.DELAY_COL] else False),
                    ('observations', '=', line_data[final_col]),
                ])

                if supplierinfo_already_exist:
                    continue

                # If there're already lines with min_qty, max_qty and
                # price equal 0, delete that lines
                supplierinfo_null_values = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', product.id),
                    ('min_qty', '=', 0),
                    ('max_quantity', '=', 0),
                    ('price', '=', 0),
                ])

                # If there's already a supplierinfo with that parameters, update it
                # Else, create a new one with all specified parameters
                if supplierinfo:
                    if supplierinfo['price'] != final_values['price']:
                        copy_supplierinfo = supplierinfo.copy()
                        supplierinfo.write({
                            'active': False,
                        })
                        copy_supplierinfo.write(final_values)
                    else:
                        supplierinfo.write(final_values)
                else:
                    if date_start:
                        final_values.update({
                            'date_start': date_start.strftime("%Y-%m-%d"),
                        })
                    if date_end:
                        final_values.update({
                            'date_end': date_end.strftime("%Y-%m-%d"),
                        })
                    final_values.update({
                        'name': supplier.id,
                        'product_tmpl_id': product.id,
                        'currency_id': currency.id,
                        'product_code': product.supplier_internal_ref,
                    })
                    final_values.update({
                        'min_qty': float(qty_values['min_qty']),
                    })
                    if qty_values['max_quantity']:
                        final_values.update({
                            'max_quantity': float(qty_values['max_quantity']),
                        })
                    new_supplier_info = self.env['product.supplierinfo'].create(final_values)
                    if not new_supplier_info:
                        raise UserError(
                            _("There's an error creating new supplierinfo in odoo with values %s")
                            % (final_values))

                    if supplierinfo_null_values:
                        supplierinfo_null_values.unlink()
            else:
                columns_without_data += 1
                if columns_without_data == len(range(self.DELAY_COL+1, final_col)):
                    raise UserError("There's no data to process in one line!")
        return 0

    def get_min_max_qty(self, value):
        min = 0
        max = 0
        is_digit = True

        for c in value:
            if c == '<' or c == '>' or c == '-':
                is_digit = False

        if is_digit:
            min = value
            max = value

        if not is_digit and value[0] == '<':
            min = '0.0'
            max = value[1:]

        if not is_digit and value[0] == '>':
            max = '0.0'
            min = value[1:]

        if not is_digit and value[0] not in ['<', '>']:
            for i in range(len(value)):
                if value[i] == '-':
                    min = value[:i]
                    max = value[(i+1):]
        return {
            'min_qty': min.replace(',', '.'),
            'max_quantity': max.replace(',', '.'),
        }
