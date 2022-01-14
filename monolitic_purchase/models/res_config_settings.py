# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    inspection_users = fields.Many2many(
        'res.users',
        related="company_id.inspection_users",
        readonly=False,
        string='Inspection Users',
        help="Users responsible of inspectioning products",
    )
