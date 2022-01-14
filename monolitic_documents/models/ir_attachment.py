# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class IrAttachemnt(models.Model):
    _inherit = 'ir.attachment'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee"
    )
    res_model = fields.Char(
        'Resource Model',
        readonly=False,
        help="The database object this attachment will be attached to."
    )
    res_id = fields.Integer(
        'Resource ID',
        readonly=False,
        help="The record id this is attached to."
    )
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        employee_obj = self.employee_id

        if employee_obj:
            self.res_model = 'hr.employee'
            self.res_id = employee_obj.id
        else:
            self.res_model = ''
            self.res_id = 0
