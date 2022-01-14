from odoo import fields, models, api, _


class crm_Claim_ept(models.Model):
    _name = "crm.claim.ept"
    _inherit = ["crm.claim.ept", "portal.mixin"]

    #     contact_partner_id = fields.Many2one('res.partner', string='Contact Person')
    #     delivery_partner_id = fields.Many2one('res.partner', string='delivery Address ')
    ## this method is use for add portal_url to RMA and its use for RMA Form Pagination.

    def _compute_access_url(self):
        super(crm_Claim_ept, self)._compute_access_url()
        for order in self:
            order.portal_url = "/my/rma/orders/%s" % (order.id)

    def get_returnable_product_quantity(self, res_id=False):
        previous_claim = (
            self.env["claim.line.ept"]
            .sudo()
            .search(
                [("product_id", "=", res_id.product_id.id), ("move_id", "=", res_id.id)]
            )
        )
        if previous_claim:
            returned_qty = 0
            for claim in previous_claim:
                returned_qty += claim.quantity
            return res_id.quantity_done - returned_qty
        else:
            return res_id.quantity_done

    def get_returnable_order(self, res_id=False):
        move = res_id.move_lines
        if move:
            display_order = False
            for m in move:
                previous_claim = (
                    self.env["claim.line.ept"]
                    .sudo()
                    .search(
                        [("product_id", "=", m.product_id.id), ("move_id", "=", m.id)]
                    )
                )
                if previous_claim:
                    returned_qty = 0
                    for claim in previous_claim:
                        returned_qty += claim.quantity
                    if returned_qty < m.quantity_done:
                        display_order = True
                else:
                    display_order = True
                if display_order == True:
                    return display_order
            return display_order
