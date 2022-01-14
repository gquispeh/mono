from odoo import models, fields


class ResPartnerActivity(models.Model):
    _name = "res.partner.activity"
    _description = "Res Partner Activity"

    name = fields.Char(string='Name', translate=True)
    partner_type = fields.Selection(
        string='Partner Type',
        selection=[('customer', 'Customer'), ('supplier', 'Supplier')]
    )
