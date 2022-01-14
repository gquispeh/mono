# -*- coding: utf-8 -*-
# Copyright 2019 Roger Escola <roger.escola@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import LDM",
    "summary": "Import Listas de Materiales",
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
        "mrp",
    ],
    "data": [
        "wizard/import_ldm.xml",
        "wizard/import_operations.xml",
        "security/ir.model.access.csv"
    ],
}
