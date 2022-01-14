# Copyright 2020 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import RMA",
    "summary": "Import RMA",
    "version": "14.0.1.0.0",
    "category": "Partner",
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
    ],
    "data": [
        "wizard/import_rma.xml",
        "security/ir.model.access.csv"
    ],
}
