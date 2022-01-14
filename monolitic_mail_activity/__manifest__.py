# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Mail Activity",
    "summary": "Monolitic changes for activities",
    "version": "14.0.1.0.1",
    "category": "Base",
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
        "mail_activity_board",
        "mail_activity_done",
        "monolitic_crm",
        "monolitic_product",
        "monolitic_hr_custom",
        "project",
    ],
    "data": [
        'data/external_id.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/mail_activity.xml',
        'views/mail_activity_subtype.xml',
        'views/res_partner.xml',
        'views/ir_actions_server.xml',
        'data/res_groups.xml',
    ],
}
