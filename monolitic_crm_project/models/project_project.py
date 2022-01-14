# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    lead_id = fields.Many2one('crm.lead',
                              'Lead')
    partner_id = fields.Many2one('res.partner',
                                 default=lambda self:
                                 self.env.get('crm.lead').browse(
                                     self._context.get('default_lead_id')
                                 ).partner_id)
