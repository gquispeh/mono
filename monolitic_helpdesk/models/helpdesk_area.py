# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskArea(models.Model):
    _name = 'helpdesk.area'
    _description = 'Helpdesk Area'

    name = fields.Char(string='Name', required=True)
    helpdesk_team_ids = fields.Many2many(
        comodel_name='helpdesk.team',
        string='Helpdesks',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned to',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'helpdesk.group_helpdesk_user').id)],
    )
