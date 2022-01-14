# Copyright 2019 QubiQ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Documents",
    "summary": "Monolitic module for Documents",
    "version": "14.0.1.0.1",
    "category": "Documents",
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
        "documents",
    ],
    "data": [
        'assets.xml',
        'views/document_view.xml'
    ],
}
