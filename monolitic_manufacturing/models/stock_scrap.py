from odoo import fields, models
# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    note = fields.Char()
