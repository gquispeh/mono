from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    adress_report_header = fields.Many2many(comodel_name='res.partner')
