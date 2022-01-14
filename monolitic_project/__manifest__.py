
{
    "name": "Monolitic Project",
    "summary": "Module Project for the Monolitic company",
    "version": "14.0.1.0.1",
    "category": "Project",
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
        "base",
        "project",
        "project_template",
    ],
    "data": [
        "data/res.groups.xml",
        "data/ir.rule.xml",
        "security/ir.model.access.csv",
        "security/project_security.xml",
        "views/res_partner.xml",
        "views/project_project.xml",
    ],
}
