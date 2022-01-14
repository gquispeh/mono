# Copyright 2020 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Import Message",
    "summary": "Import Message",
    "version": "12.0.1.0.1",
    "category": "Mail",
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
        "mail",
        "import_attachments",
        # depends only for parent menu, can be removed with a menu change
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/import_message.xml",
    ],
}
