# Copyright Daniel López 2021 <daniel.lopez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CommercialZone(models.Model):
    _name = 'commercial.zone'
    _description = 'Model for managing commercial zones'

    name = fields.Char(required=True)
