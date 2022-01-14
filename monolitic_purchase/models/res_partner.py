# Copyright 2020 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_classification = fields.Selection(
        string='Supplier Classification',
        selection=[
            ('critic', 'Estratégico Crítico'),
            ('no_critic', 'Estratégico No Crítico'),
            ('no_strat', 'No Estratégico'),
            ('no_valuable', 'No Evaluable'),
            ('creditor', 'Acreedor')],
        default='no_valuable'
    )
    register_project_protection = fields.Boolean(
        string='Project Protection and Registration'
    )
    product_category_id = fields.Many2one(
        comodel_name='product.category', string='Product Category')
    warranty = fields.Integer(string='Warranty Duration', required=True)
    warranty_type = fields.Selection(
        string='Warranty Type',
        selection=[
            ('day', 'Day(s)'),
            ('week', 'Week(s)'),
            ('month', 'Month(s)'),
            ('year', 'Year(s)')],
        default='day',
        required=True,
    )
    lead_time = fields.Integer(string='Lead Time', required=True)
    lead_time_type = fields.Selection(
        string='Lead Time Type',
        selection=[
            ('day', 'Day(s)'),
            ('week', 'Week(s)'),
            ('month', 'Month(s)'),
            ('year', 'Year(s)')],
        default='day',
        required=True,
    )
