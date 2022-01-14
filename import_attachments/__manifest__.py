# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Import Attachments",
    "summary": "Import Attachments",
    "version": "12.0.1.0.1",
    "category": "Invoicing",
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
    ],
    "data": [
        "wizards/import_attachments.xml",
        'security/ir.model.access.csv',
    ],
}
