# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    activity_category = fields.Selection(
        related='activity_type_id.category', readonly=True)

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id_custom(self):
        for rec in self:
            allow_ids = self.mapped('activity_type_id.sub_type_ids').ids
            if rec.sub_type_id and rec.sub_type_id.id not in allow_ids:
                rec.sub_type_id = False
            return {'domain': {'sub_type_id': [('id', 'in', allow_ids)]}}
