# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# Copyright 2020 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    date_previous_comment = fields.Datetime(
        string='Date previous comment',
        compute="_compute_date_previous_comment",
        store=True,
    )

    @api.depends('message_ids.res_id')
    def _compute_date_previous_comment(self):
        for rec in self:
            message_obj = self.env['mail.message'].search([
                ('message_type', '=', 'comment'),
                ('res_id', '=', rec.id),
                ('model', '=', rec._name),
            ], order='date desc')
            if message_obj:
                rec.date_previous_comment = message_obj[0].date

    probability_stand_by = fields.Float(
        string='probability_stand_by',
    )

    hide_express = fields.Boolean(
        string='Hide in OPPN Express',
    )

    team_id = fields.Many2one(default=None)
    hr_department_id = fields.Many2one(
        comodel_name='hr.department', string='HR department')
    strategic_classification = fields.Many2one(
        comodel_name='monolitic.client.classification')
    business_option = fields.Boolean(string='Business Option')
    supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Supplier',
        domain=[('is_supplier', '=', True,)])
    is_express = fields.Boolean(string="Is Express")
    partner_id = fields.Many2one(domain=[])
    start_date = fields.Datetime(
        string='Start Date',
        tracking=True,
        default=fields.Datetime.now(),
    )
    date_previous_stage = fields.Date(
        string='Date previous stage',
        tracking=True,
    )
    date_next_stage = fields.Date(
        string='Date next stage',
        default=fields.Date.context_today,
        tracking=True,
    )
    won_status = fields.Selection([
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('pending', 'Pending'),
        ('stand_by', 'Stand by')
    ])
    description_lost = fields.Text(
        string='Descripción Perdida',
        comodel_name='crm.lost.reason',
        tracking=True,
    )
    date_deadline = fields.Date()
    closing_action_id = fields.Many2one(
        string='Closing Action',
        comodel_name='crm.closing.action',
    )

    is_assembler = fields.Boolean(
        string='Is Assembler',
    )

    assembler_id = fields.Many2one(
        string='Assembler',
        comodel_name='res.partner',
        domain="[('is_company', '=', True)]"
    )

    is_engineer = fields.Boolean(
        string='Is Engineer',
    )

    engineer_id = fields.Many2one(
        string='Engineer',
        comodel_name='res.partner',
        domain="[('is_company', '=', True)]"
    )

    is_competence = fields.Boolean(
        string='Is Competence',
    )

    competence_reference = fields.Text(string="Competence Reference")

    competence_target = fields.Float(string="Competence Target")

    competence_maker = fields.Text(string="Competence Maker")

    competence_distributor = fields.Text(string="Competence Distributor")

    commercial_user_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_commercial_user_ids',
    )
    stage_id = fields.Many2one(
        domain="['|', ('hide_express', '=', False), \
            ('hide_express', '!=', is_express)]"
    )

    @api.depends('partner_id')
    def _compute_commercial_user_ids(self):
        domain = [('is_commercial', '=', True)]
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.user_id:
                    domain = [('id', 'in', self.partner_id.user_id.ids)]

            commercial_users_obj = self.env['res.users'].search(domain)
            rec.commercial_user_ids = commercial_users_obj.ids

    @api.onchange('date_next_stage')
    def onchange_date_next_stage(self):
        self.date_previous_stage = self._origin.date_next_stage

    def write(self, vals):
        if 'stage_id' in vals:
            if self.won_status == "stand_by":
                raise ValidationError(_(
                    "You can't move the stage if the Lead/Opportunity"
                    " is on Stand By !"))

            vals['date_next_stage'] = False
        return super(CrmLead, self).write(vals)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.user_id = self.partner_id.user_id[0] if self.partner_id.user_id else False
        self.strategic_classification = self.partner_id.strategic_classification if self.partner_id.strategic_classification else False
        self.hr_department_id = self.partner_id.hr_department_id if self.partner_id.hr_department_id else False
        self.team_id = self.partner_id.team_id if self.partner_id.team_id else False
        self.supplier_id = self.partner_id.supplier_id if self.partner_id.supplier_id else False
        self.commercial_zone_id = self.partner_id.commercial_zone_id if self.partner_id.commercial_zone_id else False
        self.website = self.partner_id.website if self.partner_id.website else False
        self.mobile = self.partner_id.mobile if self.partner_id.mobile else False
        self.title = self.partner_id.title if self.partner_id.title else False

    def action_set_stand_by(self):
        for lead in self:
            lead.won_status = "stand_by"
        return True

    def action_unset_stand_by(self):
        for lead in self:
            lead.won_status = "pending"
        return True

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        return super(CrmLead, self.with_context(
            mail_post_autofollow=True)).message_post(**kwargs)


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.model
    def _get_default_team_id(self):
        return False
