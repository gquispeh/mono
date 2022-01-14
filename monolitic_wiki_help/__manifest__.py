# Copyright 2020 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Wiki Help",
    "summary": "Wiki help module for Monolitic",
    "version": "14.0.1.0.1",
    "category": "Web",
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
        'views/template.xml',
        'views/ir_ui_menu.xml',
    ],
    "qweb": [
        'static/src/xml/wiki_systray.xml',
    ],
}
