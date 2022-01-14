# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _compute_partner_id(self):
        for production in self:
            if production.origin:
                prod_so = self.env['sale.order'].search([
                    ('name', '=', production.origin)])
                if prod_so:
                    production.partner_id = prod_so.partner_id
                else:
                    production.partner_id = False
            else:
                production.partner_id = False

    def _compute_interval_tracking(self):
        for production in self:
            interval_tracking_list = []
            tracking_lines = production.finished_move_line_ids.filtered(
                lambda x: x.lots_visible and x.lot_id)
            if tracking_lines:
                for tracking in tracking_lines:
                    interval_tracking_list.append(tracking.lot_id.name)
                if interval_tracking_list:
                    from_interval = min(interval_tracking_list)
                    to_inverval = max(interval_tracking_list)

                    production.interval_tracking = _(
                        'From %s to %s') % (from_interval, to_inverval)
                else:
                    production.interval_tracking = False
            else:
                production.interval_tracking = False

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        compute='_compute_partner_id',
    )
    observations = fields.Html()
    interval_tracking = fields.Char(compute='_compute_interval_tracking')
