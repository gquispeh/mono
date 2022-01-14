from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import timedelta, datetime


class ResUsers(models.Model):
    _inherit = "res.users"

    default_section_id = fields.Many2one("crm.team", string="Default Sales Team")


class CRMLead(models.Model):
    _inherit = "crm.lead"

    def _resolve_section_id_from_context(self):
        if self._context is None:
            self._context = {}
        if type(self._context.get("default_section_id")) in (int, int):
            return self._context.get("default_section_id")
        if isinstance(self._context.get("default_section_id"), str):
            section_ids = self.env["crm.team"].name_search(
                name=self._context["default_section_id"]
            )
            if len(section_ids) == 1:
                return int(section_ids[0][0])
        return None


class CRMClaimLine(models.Model):
    _name = "claim.line.ept"
    _inherit = [
        "ml.notes.mixing.rma",
        "mail.thread",
        "rating.mixin",
        "mail.activity.mixin",
    ]
    _description = "RMA Claim Line"
    _rec_name = "product_description"

    def _track_template(self, tracking):
        res = super(CRMClaimLine, self)._track_template(tracking)
        claim_line = self[0]
        # changes, tracking_value_ids = tracking[claim_line.id]
        if "ept_state_id" in tracking and claim_line.ept_state_id.template_id:
            res["ept_state_id"] = (
                claim_line.ept_state_id.template_id,
                {
                    "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"].xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "notif_layout": "mail.mail_notification_light",
                },
            )
        return res

    def get_return_quantity(self):
        for record in self:
            if record.claim_id.return_picking_id:
                # Issue: While BOM type product record occurred at that time 2 move was found, because both move have the same picking_id
                # as well sale_line_id for that reason singletone error occurred.
                # Solution: Added record product_id in domain by that filter only one move found which have same product.
                # Last change : Priya Pal 26 July 2019
                move_line = self.env["stock.move"].search(
                    [
                        ("picking_id", "=", record.claim_id.return_picking_id.id),
                        ("sale_line_id", "=", record.move_id.sale_line_id.id),
                        ("product_id", "=", record.product_id.id),
                        ("origin_returned_move_id", "=", record.move_id.id),
                    ]
                )
                record.return_qty = move_line.quantity_done
            else:
                record.return_qty = 0

    def get_done_quantity(self):
        for record in self:
            if record.claim_id.picking_id:
                record.done_qty = record.move_id.quantity_done
            else:
                record.done_qty = 0

    @api.constrains("claim_type", "claim_id")
    def check_action(self):
        for rec in self.filtered(
            lambda x: x.rma_reason_id and x.rma_reason_id.action and x.claim_type
        ):
            if rec.claim_type != rec.rma_reason_id.action:
                raise Warning(_("The action is not related with the reason"))

    @api.constrains("quantity")
    def check_qty(self):
        for line in self:
            if line.quantity < 0:
                raise Warning(_("Quantity must be positive number"))
            elif line.quantity > line.move_id.quantity_done:
                raise Warning(
                    _(
                        "Quantity must be less than or equal"
                        " to the delivered quantity"
                    )
                )

    product_id = fields.Many2one("product.product", string="Product")
    product_reference = fields.Char(related="product_id.default_code")
    product_description = fields.Text(related="product_id.description", required=True)
    product_manufacturer = fields.Many2one(related="product_id.manufacturer")
    manufacturer_rma = fields.Char(
        string="Man. RMA Code",
    )
    product_categ_id = fields.Many2one(
        related="product_id.categ_id", string="Business Unit"
    )
    done_qty = fields.Float("Delivered Quantity", compute="get_done_quantity")
    quantity = fields.Float("Return Quantity", copy=False)
    return_qty = fields.Float("Received Quantity", compute="get_return_quantity")
    claim_id = fields.Many2one(
        "crm.claim.ept", string="Related claim", copy=False, ondelete="cascade"
    )
    claim_type = fields.Selection(
        [("refund", "Refund"), ("replace", "Replace"), ("repair", "Repair")],
        "Claim Type",
        copy=False,
    )
    to_be_replace_product_id = fields.Many2one(
        "product.product", "Product to be Replace", copy=False
    )
    to_be_replace_quantity = fields.Float("Replace Quantity", copy=False)
    is_create_invoice = fields.Boolean("Create Invoice", copy=False)
    is_create_refund = fields.Boolean(string="Create Refund", copy=False)
    move_id = fields.Many2one("stock.move")
    rma_reason_id = fields.Many2one("rma.reason.ept", "Reason")
    ept_state_id = fields.Many2one(
        comodel_name="crm.claim.ept.state",
        string="State",
        tracking=True,
        required=True,
        default=lambda self: self.env.ref("rma_ept.rma_ept_state_draft"),
    )
    is_cancelled = fields.Boolean(string="")
    note = fields.Text()
    note_type = fields.Selection(
        string="Note Type",
        selection=[
            ("problem_detected", "Problem Detected"),
            ("actions_take", "Actions to Take"),
            ("technical_resolution", "Technical Resolution"),
            ("admin_resolution", "Administrative Resolution"),
            ("cancelled", "Cancel Reason"),
        ],
    )
    warranty = fields.Boolean(compute="_compute_is_warranty", store=True)
    total_amount = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_total_amount",
    )
    currency_id = fields.Many2one(related="sale_line_id.currency_id")
    price_unit = fields.Float(related="sale_line_id.price_unit")
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line", related="move_id.sale_line_id"
    )
    unique_code = fields.Char()

    def rating_get_partner_id(self):
        if self.claim_id.partner_id:
            return self.claim_id.partner_id

        return super(CRMClaimLine, self).rating_get_partner_id()

    def rating_get_rated_partner_id(self):
        if self.claim_id.user_id:
            return self.claim_id.user_id.partner_id
        return super(CRMClaimLine, self).rating_get_rated_partner_id()

    @api.depends("price_unit", "quantity")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.price_unit * rec.quantity

    @api.model
    def check_warranty(self, product_id, date_done, date_end):
        """This function check the warranty from the product
        and return True or False depens on date_done"""
        if not (product_id.warranty and date_end and date_done):
            return False
        unit = product_id.warranty
        if product_id.warranty_type == "day":
            date_done += timedelta(days=unit)
        elif product_id.warranty_type == "week":
            date_done += timedelta(days=unit * 7)
        elif product_id.warranty_type == "month":
            date_done = datetime(date_done.year, date_done.month + unit, 1) + timedelta(
                days=date_done.day
            )
        elif product_id.warranty_type == "year":
            date_done += timedelta(days=unit * 365)
        return date_done >= date_end

    @api.depends("claim_id.date")
    def _compute_is_warranty(self):
        for rec in self:
            rec.warranty = self.check_warranty(
                rec.product_id, rec.move_id.date, rec.claim_id.date
            )

    def button_edit_note(self):
        self.ensure_one()
        view = self.env.ref("rma_ept.ept_line_note_view_form")
        if self.is_cancelled and self.note_type == "cancelled":
            self.write({"note_type": False, "note": False})
        return {
            "name": _("Notas"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": self.env.context,
        }

    def button_confirm(self):
        self.write({"is_cancelled": False})

    def button_open_cancel_view(self):
        self.ensure_one()
        view = self.env.ref("rma_ept.ept_line_cancel_view_form")
        self.write({"note_type": "cancelled", "note": False, "is_cancelled": True})
        return {
            "name": _("Notas"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": self._name,
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": self.env.context,
        }

    def _compute_warranty(self):
        """Create a field in product template with the time of expiration
        Calculate warranty based on the date of the RMA's creation
        minus the Stock Picking data transfer
        """
        pass

    def write(self, vals):
        for record in self:
            msg = ""

            product_name = self.env["product.product"].search_read(
                [("id", "=", vals.get("product_id"))], ["name"]
            )
            product_name = product_name and product_name[0][1] or record.product_id.name

            if vals.get("ept_state_id"):
                if record.ept_state_id and record.ept_state_id.id != vals.get(
                    "ept_state_id"
                ):
                    new_state = self.env["crm.claim.ept.state"].browse(
                        vals.get("ept_state_id")
                    )

                    msg += _(
                        "State of %s: %s → %s\n"
                        % (product_name, record.ept_state_id.name, new_state.name)
                    )

            if vals.get("is_cancelled"):
                msg += _(
                    "Line with product %s cancelled for : %s\n"
                    % (product_name, vals.get("note", _("No reason")))
                )
            if msg:
                post_vars = {"body": msg}
                record.claim_id.message_post(message_type="comment", **post_vars)
        return super(CRMClaimLine, self).write(vals)

    @api.onchange("rma_reason_id")
    def _onchange_rma_reason_id(self):
        for rma_line in self:
            rma_line.claim_type = rma_line.rma_reason_id.action

    def unlink(self):
        for record in self:
            if record.claim_id and record.claim_id.state != "open":
                raise Warning(_("Claim Line cannot be delete once it Approved."))
        return super(CRMClaimLine, self).unlink()

    def action_claim_refund_process_ept(self):
        return {
            "name": "Return Products",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "claim.process.wizard",
            "src_model": "claim.line.ept",
            "target": "new",
            "context": {
                "product_id": self.product_id.id,
                "hide": True,
                "claim_line_id": self.id,
            },
        }


class ResUsers(models.Model):
    _inherit = "res.users"

    default_section_id = fields.Many2one("crm.team", string="Default Sales Team")


class CRMLead(models.Model):
    _inherit = "crm.lead"

    def _resolve_section_id_from_context(self):
        if self._context is None:
            self._context = {}
        if type(self._context.get("default_section_id")) in (int, int):
            return self._context.get("default_section_id")
        if isinstance(self._context.get("default_section_id"), str):
            section_ids = self.env["crm.team"].name_search(
                name=self._context["default_section_id"]
            )
            if len(section_ids) == 1:
                return int(section_ids[0][0])
        return None


class CRMClaimRejectMessage(models.Model):
    _name = "claim.reject.message"
    _description = "CRM Claim Reject Message"

    name = fields.Char("Reject Reason", required=1)


class CRMReason(models.Model):
    _name = "rma.reason.ept"
    _description = "CRM Reason"

    name = fields.Char("RMA Reason", required=1)
    action = fields.Selection(
        [("refund", "Refund"), ("replace", "Replace"), ("repair", "Repair")],
        "Related Action",
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _claim_count(self):
        for partner_id in self:
            partner_id.claim_count = self.env["crm.claim.ept"].search_count(
                [("partner_id", "=", partner_id.id)]
            )

    claim_count = fields.Integer(compute="_claim_count", string="# Claims")
