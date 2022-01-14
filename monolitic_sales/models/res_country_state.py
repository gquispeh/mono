from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone', required=True
    )
