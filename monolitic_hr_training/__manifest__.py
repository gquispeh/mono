# Copyright 2019 Jesus Ramoneda <jesus.ramonedae@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic HR Training",
    "summary": "Manage training for employeers",
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
        "contacts",
        "base_automation",
        "hr_holidays",
        "monolitic_hr_custom"
    ],
    "data": [
        'data/base_automation.xml',
        #'data/template_email.xml',
        'views/menu.xml',
        'views/training_training.xml',
        'views/training_course.xml',
        'views/hr_employee.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
}
