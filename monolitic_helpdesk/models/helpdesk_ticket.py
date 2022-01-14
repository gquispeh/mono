# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

PARTNER_TYPE = [
    ('none', 'None'),
    ('vip', 'VIP'),
    ('maint', 'Maintenance'),
    ('inc', 'Increase'),
    ('notstr', 'Not strategic'),
]
NC_TYPE = [
    ('none', 'None'),
    ('inter_nc', 'NC Interna'),
    ('customer_nc', 'Reclamación Cliente'),
    ('provider_nc', 'NC Proveedor'),
    ('audit_nc', 'NC Auditoría Interna'),
]
ACTIONS_TYPE = [
    ('immediate', 'Immediate'),
    ('corrective', 'Corrective'),
    ('preventive', 'Preventive'),
]


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    helpdesk_area_id = fields.Many2one(
        comodel_name='helpdesk.area',
        string='Helpdesk Area',
    )
    partner_type = fields.Selection(
        PARTNER_TYPE,
        string='Partner Type',
        default='none',
    )
    author_id = fields.Many2one(
        comodel_name='res.users',
        string='Author',
        tracking=True,
        default=lambda self: self.env.user,
        required=True,
    )
    conformity_type = fields.Selection(
        NC_TYPE,
        default='none',
    )
    conformity_date = fields.Date()
    description = fields.Html()
    related_ticket_id = fields.Many2one(
        comodel_name='helpdesk.ticket',
        string='Related Ticket',
    )
    is_ncc = fields.Boolean(related="team_id.is_ncc")
    error_classification_id = fields.Many2one(
        comodel_name='helpdesk.error.classification',
        string='Error Classification',
    )
    actions_type = fields.Selection(
        ACTIONS_TYPE,
        string='Actions Type',
        default=False,
    )
    action_description = fields.Text(string='Action Description')
    action_responsible_ids = fields.Many2many(
        comodel_name='res.users',
        string='Action Users')
    action_closing_date = fields.Date(string='Closing Date Action')
    action_closing_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Action Closing User')
    action_status = fields.Selection(
        string='Action Status',
        selection=[('open', 'Open'), ('closed', 'Closed')])
    evaluation_date = fields.Date(string='Evaluation Date')
    evaluation_analysis = fields.Text(string='Evaluation Analysis')
    evaluation_description = fields.Text(string='Evaluation Description')
    ticket_type_id = fields.Many2one(required=True)
    project_id = fields.Many2one(required=True)
    is_author_customer = fields.Boolean(related="team_id.is_author_customer")

    partner_ticket_count = fields.Integer(string='Partner Ticket Count', related="partner_id.ticket_count")

    @api.onchange('team_id')
    def _onchange_team_id(self):
        self.helpdesk_area_id = False

    @api.onchange('helpdesk_area_id')
    def _onchange_helpdesk_area_id(self):
        if self.helpdesk_area_id:
            self.user_id = self.helpdesk_area_id.user_id

    # Override CREATE to remove partner follower & add author
    @api.model
    def create(self, vals):
        res = super(HelpdeskTicket, self).create(vals)

        if res.partner_id:
            res.message_unsubscribe(partner_ids=res.partner_id.ids)
        if res.author_id:
            if res.team_id.is_author_customer:
                res.partner_id = res.author_id.partner_id.id
            res.message_subscribe(partner_ids=res.author_id.partner_id.ids)
        return res

    # Override WRITE to remove partner follower & add author
    # Check if the stage can be modified
    def write(self, vals):
        if vals.get('team_id') and not self.env.user.has_group('helpdesk.group_helpdesk_manager'):
            raise UserError(_("You can't change the field team_id"))

        if vals.get('stage_id'):
            for ticket in self:
                # Add Assigned to, Project Manager & Helpdesk Manager users
                allowed_user_ids = [
                    ticket.user_id.id,
                    ticket.project_id.user_id.id,
                ]
                allowed_user_ids.extend(ticket.team_id.manager_id.ids)
                current_user = self._context.get('uid')

                if current_user not in allowed_user_ids:
                    raise UserError(_(
                        'You cannot change the stage of the ticket %s! '
                        'Please contact with the responsible of the ticket.') %
                        (ticket.name)
                    )

        res = super(HelpdeskTicket, self).write(vals)

        if vals.get('partner_id'):
            self.message_unsubscribe([vals['partner_id']])
        if vals.get('author_id'):
            author_obj = self.env['res.users'].browse([vals['author_id']])
            if self.team_id.is_author_customer:
                self.partner_id = self.author_id.partner_id.id
            self.message_subscribe(author_obj.partner_id.ids)
        return res
