from odoo import models, fields, api
from ast import literal_eval


class ResPartner(models.Model):
    _inherit = "res.partner"

    rma_count = fields.Integer(compute="compute_rma", string="RMA Count")

    def compute_rma(self):
        all_partners = self.with_context(active_test=False).search(
            [("id", "child_of", self.ids)]
        )
        all_partners.read(["parent_id"])

        rma_order_groups = self.env["crm.claim.ept"].read_group(
            domain=[("partner_id", "in", all_partners.ids)],
            fields=["partner_id"],
            groupby=["partner_id"],
        )
        if rma_order_groups:
            for group in rma_order_groups:
                partner = self.browse(group["partner_id"][0])
                while partner:
                    if partner in self:
                        partner.rma_count += group["partner_id_count"]
                    partner = partner.parent_id
        else:
            for partner in self:
                partner.rma_count = 0
