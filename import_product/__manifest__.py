# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Product",
    "summary": "Import products",
    "version": "14.0.1.0.0",
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
        "base",
        "sale",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/import_product.xml",
        "wizard/import_product_category.xml",
        "wizard/import_customer_product.xml",
        "wizard/import_sequence_number_lot.xml",
    ],
}
