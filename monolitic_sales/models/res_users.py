# Copyright 2021 Jordi Jané <jordi.jane@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    commercial_target_ids = fields.One2many(
        string='Commercial Targets',
        comodel_name='commercial.target',
        inverse_name="related_user"
    )
    show_commercial_target = fields.Boolean(
        compute='_compute_show_commercial_target',
    )

    def write(self, vals):
        res = super(ResUsers, self).write(vals)

        if 'commercial_target_ids' in vals:
            for rec in self.commercial_target_ids:
                if (
                    not rec.market_segmentation_id or
                    not rec.product_segmentation_id
                ):
                    raise ValidationError(_(
                        'Market and product segmnetation are required !'))
        return res

    def _compute_show_commercial_target(self):
        current_user = self.env.user
        sales_manager = self.env.ref('sales_team.group_sale_manager')
        for rec in self:
            if rec.is_commercial:
                if current_user in sales_manager.users:
                    rec.show_commercial_target = True
                elif (
                    current_user.is_delegate and
                    rec.id in current_user.subordinate_ids.ids
                ):
                    rec.show_commercial_target = True
                elif current_user == rec.id:
                    rec.show_commercial_target = True
                else:
                    rec.show_commercial_target = False
            else:
                rec.show_commercial_target = False
