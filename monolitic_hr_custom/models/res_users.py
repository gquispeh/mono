# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_delegate = fields.Boolean(string='Is Delegate')
    is_commercial = fields.Boolean(
        string='Is Commercial',
    )
    department_id = fields.Many2one(
        string='Department',
        comodel_name='hr.department',
        compute='_compute_department_id',
    )
    replaces_id = fields.Many2one(
        string='Replaces',
        comodel_name='res.users',
    )
    subordinate_ids = fields.Many2many(
        string='Subordinates',
        comodel_name='res.users',
        relation='res_user_subordinate_rel',
        compute='_compute_subordinates'
    )
    replacement_ids = fields.Many2many(
        string='Replacement',
        comodel_name='res.users',
        relation='res_user_replacements_rel',
        compute='_compute_replacements'
    )

    def _compute_department_id(self):
        self.clear_caches()
        for usr in self:
            if usr.employee_ids:
                employee_id = usr.employee_ids[0]
                if employee_id.department_id:
                    if not usr.employee_ids.department_id.parent_id:
                        usr.department_id = usr.employee_ids.department_id
                    else:
                        usr.department_id = \
                            usr.employee_ids.department_id.parent_id

    def _compute_subordinates(self):
        self.clear_caches()
        for usr in self:
            if usr.is_delegate:
                employee_id = usr.employee_ids[0]
                subordinate_employees = self.env['hr.employee'].search([
                    ('parent_id', '=', employee_id.id)]).mapped('user_id')
                usr.subordinate_ids = subordinate_employees.ids
                # Comment for now, only works with real subordinates
                # for replace in usr.replacement_ids:
                #     usr.subordinate_ids += replace.subordinate_ids
            else:
                usr.subordinate_ids = False

    def _compute_replacements(self):
        self.clear_caches()
        for usr in self:
            replaces_obj = self.env['res.users'].search([(
                'replaces_id', '=', usr.id)])
            usr.replacement_ids = replaces_obj.ids
