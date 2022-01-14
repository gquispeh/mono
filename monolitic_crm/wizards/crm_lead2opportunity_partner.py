# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class CrmLead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

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
    )

    @api.model
    def default_get(self, fields):
        result = super(CrmLead2OpportunityPartner, self).default_get(fields)
        if self._context.get('active_id'):
            result['action'] = 'exist'
        return result

    # Total override since we want the wizard partner
    # in case lead partner is not assigned
    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner(
                    lead, self.action,
                    self.partner_id.id or lead.partner_id.id)

            lead.convert_opportunity(
                self.partner_id.id or lead.partner_id.id, [], False)

        leads_to_allocate = leads
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(
                lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate.handle_salesmen_assignment(
                user_ids, team_id=team_id)
