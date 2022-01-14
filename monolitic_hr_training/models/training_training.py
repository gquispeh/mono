# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class Training(models.Model):
    _name = 'training.training'
    _description = "Training"
    _rec_name = 'course_name'
    _inherit = ['ir.attachment', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(related="course_name.name")
    course_name = fields.Many2one(comodel_name='training.course',
                                  string='Course',
                                  required=True)
    price = fields.Float(string='Price', groups="hr.group_hr_manager")

    def default_employee_id(self):
        employee_id = self.env['hr.employee'].search([("user_id", "=",
                                                       self.env.user.id)])
        return employee_id or False

    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string='Employee',
                                  index=True,
                                  default=default_employee_id)

    user_id = fields.Many2one(comodel_name='res.users',
                              string='Responsable',
                              related="department_id.manager_id.user_id")

    department_id = fields.Many2one(string=u'Department',
                                    comodel_name='hr.department',
                                    related="employee_id.department_id",
                                    store=True)
    start_date = fields.Date(string='')
    state = fields.Selection(
                             selection=[('draft', 'Borrador'),
                                        ('to_validate', 'Pending To Validate'),
                                        ('validated', 'Validated'),
                                        ('cancel', 'Cancelled')],
                             default="draft",
                             tracking=True)
    is_pass = fields.Boolean(string='Approved', groups="hr.group_hr_manager")
    bonus_price = fields.Float(string='Bonus', groups="hr.group_hr_manager")
    grade = fields.Char(string='Grades', groups="hr.group_hr_manager")
    address_course = fields.Many2one(comodel_name='res.partner',
                                     string='Adress Course', domain="[('is_company', '=', True)]")

    def unlink(self):
        for rec in self:
            if rec.sudo().state not in ['draft', 'to_validate', 'cancel']:
                raise UserError(_("You cannot delete a validated course"))
        result = super(Training, self.sudo()).unlink()
        return result

    @api.model
    def create(self, values):
        # Add code here
        if "employee_id" not in values:
            employee_id = self.env['hr.employee'].search([("user_id", "=",
                                                           self.env.user.id)])
            if not employee_id:
                raise UserError(
                    _("There isn't a employeer related " +
                      "with your odoo user account"))
            values['employee_id'] = employee_id.id
        return super(Training, self).create(values)

    def action_approve(self):
        for rec in self:
            if rec.state == "to_validate":
                rec.state = "validated"
        return {}

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"
        return {}

    def action_confirm(self):
        for rec in self:
            rec.sudo().state = ('validated' if self.env.user == rec.user_id
                                else 'to_validate')
        return {}

    def action_draft(self):
        for rec in self:
            rec.state = "draft"
        return {}

    @api.constrains('course_name')
    def _check_course_name(self):
        for rec in self:
            count = rec.search_count([
                ('course_name', '=', rec.course_name.id),
                ('employee_id', '=', rec.employee_id.id),
            ])
            if count > 1:
                raise ValidationError(
                    _("This employee has already taken this course"))

    @api.onchange('course_name')
    def _onchange_course_name(self):
        if self.course_name:
            self.price = self.course_name.price
            if self.course_name.address_course:
                self.address_course = self.course_name.address_course


class CourseTraining(models.Model):
    _name = 'training.course'
    _description = 'Training Course'

    name = fields.Char()
    course_tags = fields.Many2many(comodel_name='training.course.tags')
    price = fields.Float()
    address_course = fields.Many2one(comodel_name='res.partner',
                                     string='Adress Course',
                                     domain=[('company_type', '=', 'company')])

    description = fields.Text(string='')


class CourseTrainingTags(models.Model):
    _name = 'training.course.tags'
    _description = 'Training Course Tags'

    name = fields.Char()
