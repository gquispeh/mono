# © 2010-2012 Andy Lu <andy.lu@elico-corp.com> (Elico Corp)
# © 2013 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2017 valentin vinagre  <valentin.vinagre@qubiq.es> (QubiQ)
# © 2020 Manuel Regidor  <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        if not self.env.context.get("import_create"):
            company = False
            if "company_id" in vals:
                company = self.env[
                    "res.company"].browse(vals.get("company_id"))
            else:
                company = self.env.company

            # MODIFIED QUBIQ: If entering from "Orders" get normal sequence
            if self.env.context.get("default_state"):
                vals['name'] = self.env[
                    'ir.sequence'].next_by_code('sale.order')
            elif not company.keep_name_so:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sale.quotation') or '/'

        return super(SaleOrder, self).create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default["name"] = "/"
        if self.origin and self.origin != "":
            default["origin"] = self.origin + ", " + self.name
        else:
            default["origin"] = self.name
        return super(SaleOrder, self).copy(default)
