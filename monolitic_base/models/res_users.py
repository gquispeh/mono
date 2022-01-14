from odoo import fields, models, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    activities_to_show = fields.Many2many('mail.activity', compute='_compute_activities_to_show')

    def _compute_activities_to_show(self):
        user = self.env.user
        commercial_activities = self.env['mail.activity'].search([('comercial_activity','=', True)])
        not_commercial_activities = self.env['mail.activity'].search([('comercial_activity','=', False)])
        if user.is_delegate:
            subordinates = self.env['hr.employee'].search([('parent_id','=',user.employee_id.id)]).user_id
            self.activities_to_show = commercial_activities.filtered(lambda x: x.user_id in subordinates) + not_commercial_activities.filtered(lambda x: x.user_id == user or x.create_uid == user)
        else:
            self.activities_to_show = commercial_activities.filtered(lambda x: x.user_id == user) + not_commercial_activities.filtered(lambda x: x.user_id == user or x.create_uid == user)
