# Copyright 2020 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Leads",
    "summary": "Import Leads",
    "version": "12.0.1.0.0",
    "category": "Partner",
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
        "crm",
        "crm_lead_code",
    ],
    "data": [
        "wizard/import_lead.xml",
        "security/ir.model.access.csv"
    ],
}
