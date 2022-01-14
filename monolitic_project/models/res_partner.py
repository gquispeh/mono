
from odoo import models, fields, api
from ast import literal_eval


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_task_count(self):
        all_partners = self.with_context(active_test=False).search([
            ('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        task_order_groups = self.env['project.task'].read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            fields=['partner_id'], groupby=['partner_id']
        )
        if task_order_groups:
            for group in task_order_groups:
                partner = self.browse(group['partner_id'][0])
                while partner:
                    if partner in self:
                        partner.task_count += group['partner_id_count']
                    partner = partner.parent_id
        else:
            self.task_count = 0

    def action_open_task(self):
        action = self.env.ref('project.action_view_task').read()[0]
        action['context'] = {}
        action['domain'] = [('partner_id', 'child_of', self.ids)]
        return action
