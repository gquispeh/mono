from odoo import models, fields


class ResPartnerJob(models.Model):
    _name = "res.partner.job"
    _description = "Res Partner Job"

    name = fields.Char(string='Name', translate=True)
