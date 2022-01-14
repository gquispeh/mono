from odoo import api, fields, models
# -*- coding: utf-8 -*-
# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    can_edit = fields.Boolean(compute="_check_user_rol", default=False)

    def _check_user_rol(self):
        self.can_edit = self.env.user.has_group('hr.group_hr_user')
