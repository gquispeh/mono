# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    required_planned_revenue = fields.Boolean(
        string='Required Planned Revenue',
    )
