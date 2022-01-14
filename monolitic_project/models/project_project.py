from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    department_id = fields.Many2one(
        string='Department',
        comodel_name='hr.department',
        compute='_compute_department_id',
        store=True,
    )

    template_id = fields.Many2one(
        'project.project',
        string='Template',
        domain="[('is_template', '=', True)]"
    )

    @api.depends('user_id')
    def _compute_department_id(self):
        for record in self:
            if record.user_id:
                record.department_id = record.user_id.department_id

    def update_department_projects(self):
        for record in self:
            if record.user_id:
                record.department_id = record.user_id.department_id

    # Override WRITE to check if the Project / User user can write
    def write(self, vals):
        if ('is_favorite' in vals or 'favorite_user_ids' in vals):
            return super(ProjectProject, self).write(vals)

        for rec in self:
            if 'user_id' in vals:
                if not (
                    self.env.user.has_group('project.group_project_manager') and
                    rec.create_uid.id != self.env.user.id
                ):
                    raise UserError(_(
                        'You cannot modify the project responsible! '
                        'Please contact with the responsible of '
                        'the project.'
                    ))

            if (
                self.env.user != rec.user_id and
                self.env.user != rec.department_id.manager_id.user_id and
                rec.create_uid.id != self.env.user.id and not
                self.env.user.sudo().has_group('project.group_project_manager')
            ):
                raise UserError(_(
                    'You cannot modify the project %s! '
                    'Please contact with the responsible of '
                    'the project.'
                ) % (rec.name))

        return super(ProjectProject, self).write(vals)

    # If a template is defined, create it from it instead
    @api.model
    def create(self, vals):
        user = self.env.user
        project_resp_group = self.env.ref('project.group_project_manager')
        if not self.env.context.get("skip_template"):
            if (
                not vals.get('template_id')
                and user not in project_resp_group.users
            ):
                raise UserError(_(
                    'Please select a template to create a project ! '
                ))

        res = super(ProjectProject, self).create(vals)

        if res.template_id:
            new_project = res.template_id.with_context(
                skip_template=True).copy(default={
                    'name': res.name,
                    'active': True,
                    'alias_name': res.alias_name,
                })
            if new_project.subtask_project_id != new_project:
                new_project.subtask_project_id = new_project.id

            # SINCE THE END DATE DOESN'T COPY OVER ON TASKS
            # (Even when changed to copy=true), POPULATE END DATES ON THE TASK
            for new_task_record in new_project.task_ids:
                for old_task_record in self.task_ids:
                    if new_task_record.name == old_task_record.name:
                        new_task_record.date_end = old_task_record.date_end

            # Delete previous project
            res.unlink()

            # OPEN THE NEWLY CREATED PROJECT FORM
            return new_project
        else:
            return res

    # Override to get task default values for user_id
    @api.model
    def _map_tasks_default_valeus(self, task, project):
        return {
            'company_id': project.company_id.id,
            'stage_id': task.stage_id.id,
            'name': task.name,
            'user_id': self.env.user.id
        }


