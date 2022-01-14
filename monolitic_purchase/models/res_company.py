# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    inspection_users = fields.Many2many(
        'res.users',
        string='Inspection Users',
    )
