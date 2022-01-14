# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Product Expenses",
    "summary": "Monolitic Product Expenses changes",
    "version": "14.0.1.0.1",
    "category": "Product Expenses",
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
        "account",
        "purchase_stock",
        "account_reports",
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/menu.xml',
        "reports/report_expenses.xml",
        "reports/report_ecoraee.xml",
        "views/account_invoice.xml",
        "views/product_category.xml",
        "views/product_template.xml",
        "views/purchase_order.xml",
        "views/res_company.xml",
        "views/account_intrastat.xml",
        "views/stock.xml",
        "wizards/report_expenses_wizard.xml",
        "wizards/report_ecoraee_wizard.xml",
    ],
}
