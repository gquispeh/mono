# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warranty = fields.Integer(string='Warranty Duration')
    warranty_type = fields.Selection([
        ('day', 'Day(s)'),
        ('week', 'Week(s)'),
        ('month', 'Month(s)'),
        ('year', 'Year(s)')],
        default='day',
        string='Warranty Type',
    )
