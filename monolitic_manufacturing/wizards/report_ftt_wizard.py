# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ImportOpeningJournal(models.TransientModel):
    _name = 'report.ftt.wizard'
    _description = "Report FTT Wizard"

    def default_start_date(self):
        return datetime.today().replace(day=1).date()

    def default_end_date(self):
        next_month = (datetime.today().replace(day=28) + timedelta(days=4))
        return (next_month - timedelta(days=next_month.day)).date()

    start_date = fields.Date(string='Start Date',
                             required=True,
                             default=default_start_date)
    end_date = fields.Date(string='End Date',
                           required=True,
                           default=default_end_date)

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValidationError(
                _("Date end must be after initial date"
                  "in range"))
