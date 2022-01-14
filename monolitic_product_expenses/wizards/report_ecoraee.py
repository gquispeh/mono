from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class EcoraeeReportWzd(models.TransientModel):
    _name = 'report.ecoraee.wizard'
    _description = 'Wizard for Generate EcoRAEE Report'

    start_date = fields.Date()
    end_date = fields.Date()

    def get_invoices_line_ecoraee(self):
        end_date = self.end_date or datetime.now().date()
        line_ids = self.env['account.move.line'].search([
            ('move_id.invoice_date', '>=', self.start_date),
            ('move_id.invoice_date', '<=', end_date),
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'posted'),
            ('product_id.ecoraee_active', '=', True)]).sorted(
                key=lambda il: il.move_id.invoice_date)
        return line_ids

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValidationError(_("Date end must be after initial date in range"))
