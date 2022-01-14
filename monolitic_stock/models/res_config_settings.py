# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    picking_note = fields.Html(related='company_id.picking_note',
                               string="Notes", readonly=False)
    use_picking_note = fields.Boolean(
        string='Default Terms & Conditions',
        config_parameter='picking_order.use_picking_note')
