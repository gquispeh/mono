# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    helpdesk_team_ids = fields.Many2many(
        comodel_name='helpdesk.team',
        string='Helpdesks',
    )
