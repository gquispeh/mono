# Copyright 2021 QubiQ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from datetime import datetime


class StockQuantHistoric(models.Model):
    _name = "stock.quant.historic"
    _description = "Stock Quant Historic"
    _inherit = "stock.quant"

    copy_date = fields.Datetime()

    def _copy_stock_quant_table(self):
        query_copy = """
            INSERT INTO stock_quant_historic
                (product_id, company_id, location_id, lot_id, package_id,
                owner_id, quantity, reserved_quantity, in_date, removal_date)
            SELECT product_id, company_id, location_id, lot_id, package_id,
                owner_id, quantity, reserved_quantity, in_date, removal_date
            FROM stock_quant
        """
        self.env.cr.execute(query_copy)

        query_date = (
            "UPDATE stock_quant_historic set copy_date = '" +
            str(datetime.now()) + "' WHERE copy_date IS NULL"
        )
        self.env.cr.execute(query_date)
