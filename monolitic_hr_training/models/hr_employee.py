# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class HREmployeeTranining(models.AbstractModel):
    _inherit = 'hr.employee.base'

    training_ids = fields.One2many(
        comodel_name='training.training',
        inverse_name='employee_id', string='Trainings')
