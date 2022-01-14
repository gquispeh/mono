# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    '''
        Override since we dont want automatic reservations
    '''
    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        # Minimum stock rules
        domain = self._get_orderpoint_domain(company_id=company_id)
        orderpoints = self.env['stock.warehouse.orderpoint'].search(domain)
        # ensure that qty_* which depends on datetime.now() are correctly
        # recomputed
        orderpoints.sudo()._compute_qty_to_order()
        orderpoints.sudo()._procure_orderpoint_confirm(
            use_new_cursor=use_new_cursor,
            company_id=company_id,
            raise_user_error=False)
        if use_new_cursor:
            self._cr.commit()

        # MODIFIED QUBIQ, WE DONT WANT AUTOMATIC RESERVATIONS
        # Search all confirmed stock_moves and try to assign them
        # domain = self._get_moves_to_assign_domain(company_id)
        # moves_to_assign = self.env['stock.move'].search(domain, limit=None,
        #     order='priority desc, date asc, id asc')
        # for moves_chunk in split_every(100, moves_to_assign.ids):
        #     self.env['stock.move'].browse(moves_chunk).sudo()._action_assign()
        #     if use_new_cursor:
        #         self._cr.commit()

        # Merge duplicated quants
        self.env['stock.quant']._quant_tasks()

        if use_new_cursor:
            self._cr.commit()
