# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    incoterm_id = fields.Many2one(
        'account.incoterms',
        string="Incoterm",
        readonly=False,
        help="International Commercial Terms are a"
        "series of predefined commercial terms"
        "used in international transactions."
    )
    intrastat_transport_mode_id = fields.Many2one(
        'account.intrastat.code',
        string='Transport',
        domain="[('type', '=', 'transport')]",
    )
    intrastat_airport_id = fields.Many2one(
        'account.intrastat.code',
        string='Port / Airport',
        domain="[('type', '=', 'airport')]",
    )