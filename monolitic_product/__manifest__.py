# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Product",
    "summary": "Monolitic Product changes",
    "version": "14.0.1.0.1",
    "category": "Product",
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
        "monolitic_category_levels",
        "product",
        "sale_stock",
        "product_supplierinfo_for_customer",
        "product_manufacturer",
    ],
    "data": [
        "data/res.groups.xml",
        'security/product_creation_group.xml',
        'security/ir.model.access.csv',
        'wizards/product_category_wizard.xml',
        'views/customer_product_code_views.xml',
        'views/product_template.xml',
        'views/product_category.xml',
        'views/res_partner_view.xml',
        'views/product_pricelist_item.xml',
        'reports/product_qr_report.xml',
    ],
}
