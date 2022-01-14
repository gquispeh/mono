# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResConfigSettings(models.Model):
    _inherit = 'res.company'

    ecorrae_perc = fields.Float(string="Ecorrae (%)")
