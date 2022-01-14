# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        ctx = self._context.copy()
        for move in self:
            if move._is_in() and self.picking_id.purchase_id:
                if self.picking_id.purchase_id.different_agreement_rate:
                    ctx.update({'rate': self.picking_id.purchase_id.rate})
        return super(StockMove, self.with_context(ctx))._action_done(
            cancel_backorder=cancel_backorder)
