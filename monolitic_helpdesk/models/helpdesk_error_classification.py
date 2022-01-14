# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskErrorClassification(models.Model):
    _name = 'helpdesk.error.classification'
    _description = 'Helpdesk Error Classification'

    name = fields.Char(string='Name', required=True)
