# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Purchase",
    "summary": "Module purchase for the Monolitic company",
    "version": "14.0.1.0.1",
    "category": "Purchase",
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
        "product",
        "purchase",
        "purchase_requisition",
        "monolitic_base",
        "monolitic_stock",
        "monolitic_product",
    ],
    "data": [
        "data/mail_activity_data.xml",
        "data/res.groups.xml",
        "security/ir.model.access.csv",
        "security/groups.xml",
        "reports/purchase_quotation_report.xml",
        "reports/purchase_order_report.xml",
        "views/product_category.xml",
        "views/product_supplierinfo.xml",
        "views/product_template.xml",
        "views/purchase_order.xml",
        "views/res_config_settings_view.xml",
        "views/res_partner.xml",
        "wizards/import_supplierinfo_wizard.xml",
    ],
}
