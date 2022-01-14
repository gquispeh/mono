from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    commercial_zone_id = fields.Many2one(
        'commercial.zone', string='Commercial Zone')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['commercial_zone_id'] = ", s.commercial_zone_id \
        as commercial_zone_id"
        groupby += ", s.commercial_zone_id"
        return super(SaleReport, self)._query(with_clause,
                                              fields, groupby, from_clause)
