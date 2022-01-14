# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Currency Rates",
    "summary": "Module to add independent currency rates to sales, purchase and invoices",
    "version": "14.0.1.0.1",
    "category": "Financial",
    "website": "https://www.qubiq.es",
    "author": "QubiQ",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "purchase",
        "sale",
        "account",
        "stock_account",
    ],
    "data": [
        "data/res_groups.xml",
        "views/purchase_order.xml",
        "views/account_invoice.xml",
        "views/sale_order.xml",
        "views/res_currency.xml",
    ],
}
