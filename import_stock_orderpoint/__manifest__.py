# Copyright 2021 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Stock Orderpoint",
    "summary": "Import Stock Orderpoint",
    "version": "12.0.1.0.0",
    "category": "Stock",
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
        "stock",
        "queue_job",
    ],
    "data": [
        "wizards/import_stock_customer_reservation.xml",
        "wizards/import_stock_orderpoint.xml",
        "security/ir.model.access.csv"
    ],
}
