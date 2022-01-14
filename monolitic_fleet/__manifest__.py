# Copyright 2020 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Fleet",
    "summary": "Monolitic Fleet",
    "version": "14.0.1.0.1",
    "category": "Fleet",
    "website": "https://www.qubiq.es",
    "author": "QubiQ",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        # "helpdesk",
        # "helpdesk_timesheet",
        "fleet",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',

    ],
}
