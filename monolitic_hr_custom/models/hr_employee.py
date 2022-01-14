# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from datetime import datetime


class HREmployeeBaseCustom(models.AbstractModel):
    _inherit = 'hr.employee.base'

    nssid = fields.Char(string='Social Security number')
    employee_code = fields.Char(string='Employee Code')
    naf = fields.Char(string='NAF')
    profesional_group = fields.Char(string='Professional Group')
    date_of_seniority = fields.Date()
    state_id = fields.Many2one(comodel_name='res.country.state')
    age_of_seniority = fields.Integer(compute="_compute_age_seniority")
    show_personal_info = fields.Boolean(
        string="Show Personal Info",
        compute="_compute_show_personal_info",
    )
    is_ocupation = fields.Boolean(string='Is Ocupation')
    contract_type = fields.Selection(string='',
                                     selection=[
                                         ('temporal', 'Temporal'),
                                         ('undefined', 'Undefined'),
                                         ('formation',
                                          'Aprendizaje y formación'),
                                     ])
    fix_instalment = fields.Float(string='Fix instalment')
    variable_instalment = fields.Float(string='Variable instalment')
    instalment_percentage = fields.Float(
        string='Instalment percentage',
        compute='_compute_instalment_percentage',
    )
    total_remuneration = fields.Float(
        string='Total remuneration',
        compute='_compute_total_remuneration',
    )
    social_security_expenses = fields.Float(string='Social security expenses')
    total_year_expenses = fields.Float(
        string='Total year expenses',
        compute='_compute_field_total_year_expenses',
    )
    skype_user = fields.Char(string="Skype User")
    gmail_user = fields.Char(string="Gmail User")
    is_delegate = fields.Boolean(
        related="user_id.is_delegate",
        store=True, compute="_compute_is_delegate"
    )
    is_commercial = fields.Boolean(
        string='Is Commercial', related="user_id.is_commercial",
        store=True, compute="_compute_is_commercial"
    )
    replaces_id = fields.Many2one(
        comodel_name='res.users', string='Replaces',
        related="user_id.replaces_id", store=True,
        compute="_compute_replaces_id"
    )

    # Hide some private fields from filter, group and export
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        hide = [
            'country_id', 'identification_id', 'nssid', 'passport_id',
            'bank_account_id', 'address_home_id', 'state_id',
            'emergency_contact', 'emergency_phone', 'km_home_work', 'gender',
            'age', 'marital', 'children', 'birthday', 'place_of_birth',
            'country_of_birth', 'visa_no', 'permit_no', 'visa_expire',
            'fix_instalment', 'variable_instalment', 'total_remuneration',
            'instalment_percentage', 'social_security_expenses',
            'date_of_seniority', 'age_of_seniority', 'resource_calendar_id',
            'contract_type', 'certificate', 'study_field', 'study_school',
            'additional_note',
        ]
        res = super(HREmployeeBaseCustom, self).fields_get(allfields, attributes=attributes)
        for field in hide:
            if field in res:
                res[field]['searchable'] = False
                res[field]['sortable'] = False
                res[field]['exportable'] = False
        return res

    @api.depends("user_id.is_commercial")
    def _compute_is_commercial(self):
        for rec in self:
            rec.is_commercial = rec.user_id.is_commercial

    @api.depends("user_id.is_delegate")
    def _compute_is_delegate(self):
        for rec in self:
            rec.is_delegate = rec.user_id.is_delegate

    @api.depends("user_id.replaces_id")
    def _compute_replaces_id(self):
        for rec in self:
            rec.replaces_id = rec.user_id.replaces_id

    @api.depends('variable_instalment', 'fix_instalment')
    def _compute_instalment_percentage(self):
        for rec in self:
            rec.instalment_percentage = 0
            if rec.fix_instalment != 0:
                rec.instalment_percentage = (rec.variable_instalment /
                                             rec.fix_instalment) * 100

    @api.depends('variable_instalment', 'fix_instalment')
    def _compute_total_remuneration(self):
        for rec in self:
            rec.total_remuneration = rec.variable_instalment +\
                rec.fix_instalment

    @api.depends('social_security_expenses', 'total_remuneration')
    def _compute_field_total_year_expenses(self):
        for record in self:
            record.total_year_expenses = record.social_security_expenses +\
                record.total_remuneration

    @api.depends('date_of_seniority')
    def _compute_age_seniority(self):
        date_now = datetime.now().date()
        for rec in self:
            if not rec.date_of_seniority:
                rec.age_of_seniority = 0
            else:
                rec.age_of_seniority = int(
                    (date_now - rec.date_of_seniority).days / 365)

    def _compute_show_personal_info(self):
        current_user = self.env['res.users'].browse([self.env.uid])
        group_hr_manager = self.env.ref('monolitic_hr_custom.group_private_information_view')

        for rec in self:
            if current_user in group_hr_manager.users:
                rec.show_personal_info = True
            elif current_user == rec.user_id:
                rec.show_personal_info = True
            else:
                rec.show_personal_info = False

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        return super(HREmployeeCustom, self.with_context(
            mail_post_autofollow=True)).message_post(**kwargs)


class HREmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    age = fields.Integer(string='Age', compute="_compute_age")

    @api.depends('birthday')
    def _compute_age(self):
        date_now = datetime.now().date()
        for rec in self:
            if not rec.birthday:
                rec.age = 0
            else:
                rec.age = int((date_now - rec.birthday).days / 365)