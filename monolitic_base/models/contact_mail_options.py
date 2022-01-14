from odoo import models, api, fields


class ResPartner(models.Model):
    _name = 'contact.mail.options'
    _description = 'Contact Mail Options'

    name = fields.Char(
        string='name',
    )
