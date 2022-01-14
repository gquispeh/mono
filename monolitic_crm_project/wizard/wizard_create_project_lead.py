# Copyright 2014-2018 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import api, fields, models


class CreateProjectWizard(models.TransientModel):
    _name = "create.crm.project.wizard"
    _description = "Lead Project Creation"

    @api.model
    def _get_default_partner(self):
        lead_id = self.env.context.get('lead_id', False)
        if lead_id:
            return self.env.get('crm.lead').browse(lead_id).partner_id

    name = fields.Char("Name", required=True)
    privacy_visibility = fields.Selection([
        ('followers', 'On invitation only'),
        ('employees', 'Visible by all employees'),
        ('portal', 'Visible by following customers'),
    ],
        string='Privacy', required=True,
        default='portal')
    rating_status_period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bimonthly', 'Twice a Month'),
        ('monthly', 'Once a Month'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], 'Rating Frequency')
    user_id = fields.Many2one('res.users',
                              string='Project Manager',
                              default=lambda self: self.env.user)
    resource_calendar_id = fields.Many2one(
        'resource.calendar',
        string='Working Time',
        default=lambda self: self.env.company.resource_calendar_id.id)
    date_start = fields.Date(string='Start Date')
    date = fields.Date(string='Expiration Date')
    type_ids = fields.Many2many('project.task.type',
                                string='Tasks Stages')
    color = fields.Integer(string='Color Index')
    rating_status = fields.Selection(
        [('stage', 'Rating when changing stage'),
         ('periodic', 'Periodical Rating'),
         ('no', 'No rating')],
        'Customer(s) Ratings',
        default="no",
        required=True)
    portal_show_rating = fields.Boolean('Rating visible publicly',
                                        copy=False)
    partner_id = fields.Many2one('res.partner',
                                 string='Customer',
                                 default=lambda self: self._get_default_partner())

    def create_project(self):
        self.env['project.project'].create({
            'name': self.name,
            'user_id': self.user_id.id,
            'rating_status_period': self.rating_status_period,
            'privacy_visibility': self.privacy_visibility,
            'resource_calendar_id': self.resource_calendar_id.id,
            'date_start': self.date_start,
            'date': self.date,
            'lead_id': (self._context.get('lead_id', False) or
                        self._context.get('active_id')),
            'type_ids': self.type_ids.ids,
            'color': self.color,
            'rating_status': self.rating_status,
            'portal_show_rating': self.portal_show_rating,
            'partner_id': self.partner_id.id
        })
