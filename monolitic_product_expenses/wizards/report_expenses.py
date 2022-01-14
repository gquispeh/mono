from odoo import fields, models
from datetime import datetime
import locale
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ModuleName(models.TransientModel):
    _name = 'report.expense.wizard'
    _description = 'Wizard for Generate Expense Report'

    start_date = fields.Date()
    end_date = fields.Date()

    def format_float(self, value):
        locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
        return locale.format("%.2f", value, grouping=True)

    def get_supplier_list(self):
        end_date = self.end_date or datetime.now().date()
        suppliers = self.env['account.move'].search_read(
            [('invoice_date', '>=', self.start_date),
             ('invoice_date', '<=', end_date),
             ('move_type', 'in', ['in_invoice', 'in_refund']),
             ('state', '=', 'posted')], ['partner_id'])

        if not suppliers:
            raise UserError(
                'No valid invoices could be found within those dates!')

        suppliers = list(map(lambda y: y['partner_id'], suppliers))
        suppliers_ids = list(map(lambda z: z[0], suppliers))
        suppliers_names = list(map(lambda z: z[1], suppliers))
        suppliers_ids, suppliers_names = [
            list(set(suppliers_ids)),
            list(set(suppliers_names))
        ]
        return dict(zip(suppliers_ids, suppliers_names))

    def get_invoice_supplier(self, supplier):
        end_date = self.end_date or datetime.now().date()
        invoice_ids = self.env['account.move'].search([
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', end_date),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('partner_id', '=', supplier)])
        return invoice_ids
