# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class PartnerXlsx(models.AbstractModel):
    _name = 'report.monolitic_manufacturing.report_ftt'
    _description = 'Report Monolitic Manufacturing FTT'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        obj = wizard[0]
        start_date = datetime.combine(obj.start_date, datetime.min.time())
        end_date = datetime.combine(obj.end_date, datetime.min.time())
        sheet = workbook.add_worksheet("FTT %s - %s" %
                                       (obj.start_date.strftime("%d-%m-%Y"),
                                        obj.end_date.strftime("%d-%m-%Y")))
        bold = workbook.add_format({'bold': True})
        # STATIC HEADER
        sheet.write(0, 0, "Producto", bold)
        sheet.write(0, 1, "Cantidad por equipo", bold)
        sheet.write(0, 2, "SCRAP", bold)
        sheet.write(0, 3, "Pedidos de Venta", bold)
        sheet.write(0, 4, "Orden Fabricación", bold)
        sheet.write(0, 5, "Observaciones", bold)
        sheet.write(0, 6, "Equipos Facturados", bold)
        sheet.write(0, 7, "Equipo-KIT", bold)
        row = 1
        mpr_production_ids = self.env['mrp.production'].search([
            ('state', '=', 'done'), ('date_finished', '>=', start_date),
            ('date_finished', '<=', end_date), ('origin', '!=', False)
        ])
        for mrp_id in mpr_production_ids:
            for i, mrp_line in enumerate(mrp_id.move_raw_ids):
                scrap_qty = self.env['stock.scrap'].search_read(
                    [('production_id', '=', mrp_id.id),
                     ('product_id', '=', mrp_line.product_id.id)],
                    ['scrap_qty', 'note'])
                sheet.write(row, 0, mrp_line.product_id.name)
                sheet.write(row, 1, mrp_line.quantity_done)
                if scrap_qty:
                    sheet.write(row, 2, scrap_qty[0]['scrap_qty'])
                    sheet.write(row, 5, scrap_qty[0]['note'] or "")
                if i == 0:
                    query = """SELECT sum(il.quantity) FROM account_move i
                        LEFT JOIN account_invoice_line il
                        ON i.id = il.invoice_id
                        WHERE il.product_id = %s AND i.origin = %s
                        AND i.state not in ('draft','cancel')"""
                    params = (mrp_id.product_id.id, mrp_id.origin)
                    self.env.cr.execute(query, params)
                    res = self.env.cr.fetchall()
                    if res:
                        sheet.write(row, 6, res[0][0])
                    sheet.write(row, 3, mrp_id.origin)
                    sheet.write(row, 4, mrp_line.origin)
                    sheet.write(row, 7, mrp_id.product_id.name)
                row += 1
