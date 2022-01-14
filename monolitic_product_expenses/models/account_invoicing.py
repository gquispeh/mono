# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class AccountMove(models.Model):
    _inherit = 'account.move'

    doc_number = fields.Char(string='Nº Document',
                             related="purchase_id.doc_number",
                             readonly=False)
    total_expenses = fields.Float(compute="get_total_expenses")
    total_expected_expenses = fields.Float(
        compute="get_total_expected_expenses")
    total_import_material = fields.Float(compute="get_total_untaxed_amount")
    total_import_invoice = fields.Float(compute="get_total_invoice_amount")
    total_ecorae = fields.Float(compute="get_total_ecorae")
    total_arancel = fields.Float(compute="get_total_arancel")
    total_cost_delivery = fields.Float(compute="get_total_delivery")
    total_cost_delivery_expected = fields.Float(
        compute="get_total_delivery_expected")

    def get_total_invoice_amount(self):
        for rec in self:
            total_invoice_amount = rec.amount_total
            if rec.currency_id != rec.env.company.currency_id:

                rates = rec.currency_id._get_rates(
                    rec.env.company,
                    rec.invoice_date,
                )
                rates = rates.get(rec.currency_id.id)
                total_invoice_amount = total_invoice_amount * rates
            rec.total_import_invoice = round(total_invoice_amount, 2)

    def get_total_untaxed_amount(self):
        for rec in self:
            total_invoice_amount = rec.amount_untaxed
            if rec.currency_id != rec.env.company.currency_id:
                rates = rec.currency_id._get_rates(
                    rec.env.company,
                    rec.invoice_date,
                )
                rates = rates.get(rec.currency_id.id)
                total_invoice_amount = total_invoice_amount * rates
            rec.total_import_material = round(total_invoice_amount, 2)

    def get_total_expenses(self):
        inv_expense = 0
        for rec in self:
            inv_expense = sum(rec.invoice_line_ids.mapped('total_expense'))
            if rec.currency_id != rec.env.company.currency_id:
                rates = rec.currency_id._get_rates(
                    rec.env.company,
                    rec.invoice_date,
                )
                rates = rates.get(rec.currency_id.id)
                inv_expense = inv_expense * rates
            rec.total_expenses = round(inv_expense, 2)

    def get_total_expected_expenses(self):
        for rec in self:
            inv_exp_expense = 0
            for line in rec.invoice_line_ids:
                if line.product_id.categ_id and line.price_unit:
                    inv_exp_expense += (
                        line.estimated_perc *
                        line.quantity * line.price_unit / 100)
            if rec.currency_id != rec.env.company.currency_id:
                rates = rec.currency_id._get_rates(
                    rec.env.company,
                    rec.invoice_date)
                rates = rates.get(rec.currency_id.id)
                inv_exp_expense = inv_exp_expense * rates
            rec.total_expected_expenses = round(inv_exp_expense, 2)

    def get_total_ecorae(self):
        for rec in self:
            ecorrae_perc = rec.company_id.ecorrae_perc
            inv_ecorae_expense = 0
            for line in rec.invoice_line_ids:
                if not line.product_id.ecoraee_active or not line.price_unit:
                    rec.total_ecorae = inv_ecorae_expense
                    continue
                inv_ecorae_expense += ((line.price_unit * line.quantity) *
                                       (ecorrae_perc / 100))
                if rec.currency_id != rec.env.company.currency_id:
                    rates = rec.currency_id._get_rates(
                        rec.env.company,
                        rec.invoice_date)
                    rates = rates.get(rec.currency_id.id)
                    inv_ecorae_expense = inv_ecorae_expense * rates
                rec.total_ecorae = round(inv_ecorae_expense, 2)

    def get_total_arancel(self):
        for rec in self:
            inv_arancel_expense = 0
            for line in rec.invoice_line_ids:
                if line.product_id.intrastat_id.rate:
                    inv_arancel_expense += ((line.price_unit * line.quantity) *
                                            (line.product_id.intrastat_id.rate /
                                            100))
                if rec.currency_id != rec.env.company.currency_id:
                    rates = rec.currency_id._get_rates(
                        rec.env.company,
                        rec.invoice_date)
                    rates = rates.get(rec.currency_id.id)
                    inv_arancel_expense = inv_arancel_expense * rates
                rec.total_arancel = round(inv_arancel_expense, 2)

    def get_total_delivery(self):
        for rec in self:
            rec.total_cost_delivery = (rec.total_expenses - rec.total_ecorae
                                       - rec.total_arancel)

    def get_total_delivery_expected(self):
        for rec in self:
            rec.total_cost_delivery_expected = round((
                rec.total_expected_expenses - rec.total_ecorae
                - rec.total_arancel), 2)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    estimated_perc = fields.Float(
        string="Estimated Import Cost (%)",
        readonly=True,
    )
    real_perc = fields.Float(
        string="Real Import Cost (%)",
    )
    total_expense = fields.Float(
        digits='Product Price',
        string="Import Expenses",
        readonly=True,
    )

    @api.onchange('quantity', 'price_unit', 'real_perc')
    def _onchange_price_expenses(self):
        for line in self:
            line.total_expense = (
                line.price_unit * line.quantity * line.real_perc / 100
            )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountMoveLine, self)._onchange_product_id()
        if not self.product_id:
            return res
        else:
            self.estimated_perc = self.product_id.categ_id.estimate_cost
        return res
