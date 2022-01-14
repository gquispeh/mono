# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class CrmLead2OpportunityPartnerMass(models.TransientModel):
    _inherit = ['crm.lead2opportunity.partner.mass']

    date_deadline = fields.Date(
        'Expected Closing',
        default=fields.Date.context_today,
        help="Estimate of the date on which the opportunity will be won.",
        required=True,
    )
    date_next_stage = fields.Date(
        string='Date next stage',
        default=fields.Date.context_today,
        required=True,
    )
    action = fields.Selection(
        readonly=True,
        default='each_exist_or_create',
    )
