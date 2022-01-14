
from odoo import models, api, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    allowed_user_ids = fields.Many2many(groups="base.group_no_one")

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        return super(ProjectTask, self.with_context(
            mail_post_autofollow=True)).message_post(**kwargs)
