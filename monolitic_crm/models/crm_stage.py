# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    hide_express = fields.Boolean(
        string='Hide in OPPN Express',
    )
