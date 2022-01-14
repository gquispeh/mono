# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    picking_note = fields.Html(string='Picking Notes')
    client_code = fields.Char(string='Client Code')
