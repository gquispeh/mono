# Copyright Xavier Jiménez 2021 <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ClosingAction(models.Model):
    _name = 'crm.closing.action'
    _description = 'Model for managing closing action for CRM'

    name = fields.Char(required=True, translate=True)
