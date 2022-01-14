# © 2016 OdooMRP team
# © 2016 AvanzOSC
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 ForgeFlow S.L. (https://forgeflow.com)
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    commitment_date = fields.Datetime("Delivery Date")

    # MODIFIED QUBIQ
    # Update sale order commitment date with the closest line date
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        # Force commitment date only if all lines are on the same sale order
        if len(self.mapped('order_id')) == 1:
            for line in self:
                if (
                    line.commitment_date
                    and not line.order_id.commitment_date
                ):
                    line.order_id.commitment_date = line.commitment_date
                elif (
                    line.commitment_date
                    and line.order_id.commitment_date
                    and line.commitment_date < line.order_id.commitment_date
                ):
                    line.order_id.commitment_date = line.commitment_date
        return res

    # MODIFIED QUBIQ
    # Update sale order commitment date with the closest line date
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        for rec in res:
            if (
                rec.commitment_date
                and not rec.order_id.commitment_date
                and rec.commitment_date < rec.order_id.commitment_date
            ):
                rec.order_id.commitment_date = rec.commitment_date
        return res

    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        # has ensure_one already
        if self.commitment_date:
            vals.update({
                "date_deadline": self.commitment_date,
                "date": self.commitment_date,
            })
        return vals
