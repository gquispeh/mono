# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hr_department_id = fields.Many2one(
        comodel_name='hr.department', string='HR department')
    strategic_classification = fields.Many2one(
        comodel_name='monolitic.client.classification',
        string='Strategic Classification')
    segmentation_ids = fields.Many2many(
        comodel_name='monolitic.client.segmentation',
        string='Segmentations')
    business_option = fields.Boolean(string='Business Option')
    supplier_id = fields.Many2one(
        comodel_name='res.partner', string='Supplier',
        domain=[('is_supplier', '=', True)])
    user_id = fields.Many2many(
        'res.users', domain="[('is_commercial', '=', True)]")

    def name_get(self):
        result = []
        origin = super(ResPartner, self).name_get()
        orig_name = dict(origin)
        for rec in self:
            name = ""
            value = orig_name[rec.id]
            name = value
            result.append((rec.id, name))
        return result
