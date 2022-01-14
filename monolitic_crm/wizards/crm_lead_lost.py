# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class CrmLeadLost(models.TransientModel):
    _inherit = ['crm.lead.lost']

    description_lost = fields.Text(
        string='Lost Description',
        comodel_name='crm.lost.reason',
        tracking=True,
        required=True
    )

    def action_lost_reason_apply(self):
        res = super(CrmLeadLost, self).action_lost_reason_apply()
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.description_lost = self.description_lost
        return res
