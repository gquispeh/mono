# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Timesheet",
    "summary": "Module timesheet for the Monolitic company",
    "version": "14.0.1.0.1",
    "category": "Timesheet",
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
        "hr_timesheet",
        "helpdesk_timesheet",
        "timesheet_grid",
    ],
    "data": [
        "views/account_analytic_line.xml",
        "views/helpdesk_ticket.xml",
        "views/project_task.xml",
    ],
}
