# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    count_project = fields.Integer(string='Projects quantity',
                                   compute='_compute_count_project')

    def _compute_count_project(self):
        for lead in self:
            lead.count_project = len(
                self.env['project.project'].search([
                    ('lead_id', '=', lead.id)])
            )
