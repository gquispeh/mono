# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Helpdesk",
    "summary": "Monolitic Helpdesk",
    "version": "14.0.1.0.1",
    "category": "Helpdesk",
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
        "helpdesk",
        "helpdesk_timesheet",
    ],
    "data": [
        "data/ir.rule.xml",
        "security/ir.model.access.csv",
        "views/helpdesk_area_view.xml",
        "views/helpdesk_error_classification.xml",
        "views/helpdesk_ticket_type_view.xml",
        "views/helpdesk_ticket_view.xml",
        "views/helpdesk_team_view.xml",
        "views/res_partner_view.xml",
        #"wizards/helpdesk_ticket_form.xml",
    ],
}
