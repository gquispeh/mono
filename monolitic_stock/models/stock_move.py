# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Get the FIFO of each move line since its computed there
    def _compute_quant_sequence_fifo(self):
        for move in self:
            sequence_fifo = move.move_line_ids.mapped(
                'quant_sequence_fifo.fifo_name')
            move.quant_sequence_fifo = " ".join(sequence_fifo)

    quant_sequence_fifo = fields.Char(
        string='FIFO', compute='_compute_quant_sequence_fifo')

    sale_link_id = fields.Many2one(
        string='Sale order',
        comodel_name='sale.order',
        compute="_compute_sale_order"
    )
    purchase_link_id = fields.Many2one(
        string='Purchase order',
        comodel_name='purchase.order',
        compute="_compute_purchase_order"
    )

    def _compute_sale_order(self):
        for rec in self:
            rec.sale_link_id = False
            if rec.sale_line_id:
                rec.sale_link_id = rec.sale_line_id.order_id.id

    def _compute_purchase_order(self):
        for rec in self:
            rec.purchase_link_id = False
            if rec.purchase_line_id:
                rec.purchase_link_id = rec.purchase_line_id.order_id.id

    # Inherit action assign function to compute the FIFO
    # Check action_cancel for unreserve FIFO
    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            for ml in move.move_line_ids:

                # Get eligible quants
                quant = self.env['stock.quant']._gather(
                    ml.product_id, ml.location_id, ml.lot_id,
                    ml.package_id, ml.owner_id, strict=True
                )
                sequence_list = []
                ml_qty = ml.qty_done

                # For each sequence assign qty based on the demand
                for seq in quant.quant_sequence_ids.filtered(
                        lambda x: x.quantity).sorted(lambda x: x.sequence):
                    remaining_qty = ml_qty - seq.quantity

                    if remaining_qty <= 0:
                        seq.quantity -= ml_qty
                        sequence_list.append(seq.id)
                        break
                    elif remaining_qty > 0:
                        seq.quantity = 0
                        ml_qty = remaining_qty
                        sequence_list.append(seq.id)
                        continue
                ml.quant_sequence_fifo = [(6, 0, sequence_list)]

        return res

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['delivery_conditions'] = self.mapped(
            'sale_line_id.order_id.delivery_conditions_id').id
        return vals
