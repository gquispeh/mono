# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def delete_duplicated_attendace_cron(self):
        attendace_obj = self.env["hr.attendance"].search([(
            "check_out", "=", False)])

        for attendace in attendace_obj:
            duplicated = self.env["hr.attendance"].search([
                ('employee_id', '=', attendace.employee_id.id),
                ('check_in', '=', attendace.check_in)
            ])
            if len(duplicated) > 1:
                attendace.unlink()

    # The user can't modify the employee the check in or check out
    # Only if it has value before
    def write(self, vals):
        if not self.env.user.has_group(
                'hr_attendance.group_hr_attendance_manager'):

            if 'employee_id' in vals:
                if self.employee_id:
                    raise UserError(_(
                        'The employee can''t be modified!'))

            if 'check_in' in vals:
                if self.check_in:
                    raise UserError(_(
                        'The check-in date can''t be modified!'))

            if 'check_out' in vals:
                _logger.info(self.check_out)
                if self.check_out:
                    raise UserError(_(
                        'The check-out date can''t be modified!'))

        return super(HrAttendance, self).write(vals)
