# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

TICKET_PRIORITY = [
    ('0', 'All'),
    ('1', 'Low priority'),
    ('2', 'High priority'),
    ('3', 'Urgent'),
]
PARTNER_TYPE = [
    ('none', 'None'),
    ('vip', 'VIP'),
    ('maint', 'Maintenance'),
    ('inc', 'Increase'),
    ('notstr', 'Not strategic'),
]


class HelpdeskTicketForm(models.TransientModel):
    _name = 'helpdesk.ticket.form'
    _description = 'Helpdesk Ticket Form'

    helpdesk_id = fields.Many2one(
        comodel_name='helpdesk.team',
        string='Helpdesk',
        required=True,
    )
    helpdesk_area_id = fields.Many2one(
        comodel_name='helpdesk.area',
        string='Helpdesk Area',
    )
    priority = fields.Selection(
        TICKET_PRIORITY,
        string='Priority',
        default='0',
    )
    partner_type = fields.Selection(
        PARTNER_TYPE,
        string='Partner Type',
        default='none',
    )
    partner_code = fields.Char(string='Partner code')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    ticket_type_id = fields.Many2one(
        comodel_name='helpdesk.ticket.type',
        string='Ticket Type',
        required=True,
    )
    author_id = fields.Many2one(
        comodel_name='res.users',
        string='Author',
        default=lambda self: self.env.user,
        required=True,
    )
    comment = fields.Html(string='Comments')

    # def generate_ticket_from_form(self):
    #     if self.helpdesk_area_id:
    #         ticket_name = self.helpdesk_area_id.name
    #     else:
    #         ticket_name = self.helpdesk_id.name
    #     ticket_name + ' - ' + self.ticket_type_id.name

    #     ticket_vals = {
    #         'name': ticket_name,
    #         'team_id': self.helpdesk_id.id,
    #         'helpdesk_area_id': self.helpdesk_area_id.id,
    #         'author_id': self.author_id.id,
    #         'user_id': (
    #             self.helpdesk_id.member_ids[0].id if
    #             self.helpdesk_id.member_ids else False),
    #         'priority': self.priority,
    #         'partner_type': self.partner_type,
    #         'partner_code': self.partner_code,
    #         'partner_id': self.partner_id.id,
    #         'project_id': self.helpdesk_id.project_id.id,
    #         'ticket_type_id': self.ticket_type_id.id,
    #         'description': self.comment,
    #     }
    #     ticket_obj = self.env['helpdesk.ticket'].create(ticket_vals)

    #     return {
    #         'name': "Ticket",
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'views': [[self.env.ref(
    #             'helpdesk.helpdesk_ticket_view_form').id, 'form']],
    #         'res_model': 'helpdesk.ticket',
    #         'res_id': ticket_obj.id,
    #     }
