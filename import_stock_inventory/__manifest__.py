# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Stock Inventory",
    "summary": "Import Stock Inventory",
    "version": "11.0.1.0.0",
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
        "base",
        "stock",
        "queue_job",
    ],
    "data": [
        "wizards/import_stock_inventory.xml",
        "wizards/update_stock_dates.xml",
        "security/ir.model.access.csv"
    ],
}
