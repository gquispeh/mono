# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)

        for rec in self:
            if 'partner_id' in vals:
                activities = self.env['mail.activity'].search([
                    ('res_id', '=', rec.id),
                    ('res_model', '=', self._name),
                ])
                activities.write({
                    'organisation_id': rec.partner_id.id or False,
                })
        return res
