# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class CrmLeadConvert2Ticket(models.TransientModel):
    _name = "crm.lead.convert2ticket"
    _description = "CRM Lead Convert To Ticket"

    @api.model
    def default_get(self, fields):
        result = super(CrmLeadConvert2Ticket, self).default_get(fields)
        active_id = self.env.context.get('active_id')

        if active_id:
            lead_obj = self.env['crm.lead'].browse([active_id])
            result['lead_id'] = active_id
            result['name'] = lead_obj.name
            result['user_id'] = self.env.uid
        return result

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead',
        domain=[('type', '=', 'lead')],
    )
    helpdesk_id = fields.Many2one(
        'helpdesk.team',
        string="Helpdesk",
        required=True,
    )
    name = fields.Char(
        string="Ticket Name",
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string="Assign To",
        tracking=True,
    )

    def lead_convert2ticket(self):
        self.ensure_one()
        lead = self.lead_id
        ticket_values = {
            'name': self.name,
            'team_id': self.helpdesk_id.id,
            'user_id': self.user_id.id,
            'partner_id': lead.partner_id.id,
            'description': lead.description,
            'lead_id': lead.id,
        }
        ticket = self.env['helpdesk.ticket'].create(ticket_values)
        # Move the mail thread and attachments
        lead.message_change_thread(ticket)
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'crm.lead'),
            ('res_id', '=', lead.id)
        ])
        attachments.write({
            'res_model': 'helpdesk.ticket', 'res_id': ticket.id
        })
        # Archive the lead
        lead.write({'active': False})
        # Return the action to go to the form view of the new Ticket
        view = self.env.ref('helpdesk.helpdesk_ticket_view_form')

        return {
            'name': 'Ticket created',
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'helpdesk.ticket',
            'type': 'ir.actions.act_window',
            'res_id': ticket.id,
            'context': self.env.context
        }
