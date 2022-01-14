# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic HR Custom",
    "summary": "Manage information about employeers",
    "version": "14.0.1.0.1",
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
        "hr",
        "hr_holidays",
        "hr_attendance",
        "hr_attendance_reason",
        "hr_appraisal",
        "hr_contract",
    ],
    "data": [
        'data/ir_rule.xml',
        'data/res.groups.xml',
        'views/hr_attendance.xml',
        'views/hr_employee.xml',
        'views/res_users.xml',
    ],
}
