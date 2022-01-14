# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    name = fields.Char(required=True)


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    name = fields.Char(required=True)
