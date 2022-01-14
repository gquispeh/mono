# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.model
    def default_get(self, field_list):
        result = super(AccountAnalyticLine, self).default_get(field_list)
        if field_list and result.get("user_id"):
            result["author_id"] = (
                self.env["hr.employee"]
                .search([("user_id", "=", result["user_id"])], limit=1)
                .id
            )
        return result

    rma_id = fields.Many2one("crm.claim.ept", string="RMA")
    author_id = fields.Many2one("hr.employee", string="Author")

    @api.model
    def create(self, vals):
        if vals.get("rma_id") and not vals.get("account_id"):
            rma = self.env["crm.claim.ept"].browse(vals.get("rma_id"))
            vals["account_id"] = rma.analytic_account_id.id
            vals["company_id"] = rma.analytic_account_id.company_id.id
        if not vals.get("author_id") and vals.get("rma_id"):
            if vals.get("user_id"):
                ts_user_id = vals["user_id"]
            else:
                ts_user_id = self._default_user()
            vals["author_id"] = (
                self.env["hr.employee"]
                .search([("user_id", "=", ts_user_id)], limit=1)
                .id
            )
        return super(AccountAnalyticLine, self).create(vals)
