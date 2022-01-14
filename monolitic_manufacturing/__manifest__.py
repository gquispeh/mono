# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Manufacturing",
    "summary": "Module manufacturing for the Monolitic company",
    "version": "14.0.1.0.1",
    "category": "MRP",
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
        "mrp",
        "monolitic_base",
        "monolitic_stock",
        "report_xlsx",
        "product_manufacturer"
    ],
    "data": [
        "data/manufacturing_groups.xml",
        "security/ir.model.access.csv",
        "reports/paperformat_mrporder.xml",
        'reports/report_ftt.xml',
        "reports/report_mrporder.xml",
        "views/mrp_production.xml",
        'views/stock_scrap_form_view.xml',
        'wizards/report_ftt_wizard.xml',
        'views/mrp_production.xml',
        'views/mrp_routing_workcenter.xml',
        'views/mrp_bom_views.xml',
        'reports/report_product_actual_stock.xml',
        'security/ir.model.access.csv'
    ]
}
