# Copyright 2019 Jesus Ramoneda <jesus.ramonedae@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Base",
    "summary": "Module base for the Monolitic company",
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
        "contacts",
        "l10n_es_partner",
        "mail",
        "partner_manual_rank",
        "account_financial_risk",
    ],
    "data": [
        "data/res_partner_activity.xml",
        "data/res.groups.xml",
        "data/ir.rule.xml",
        'security/ir.model.access.csv',
        'security/security.xml',
        "views/res_company.xml",
        "views/ml_notes.xml",
        "views/res_partner_view.xml",
        "views/res_partner_activity.xml",
        "views/contact_mail_options_view.xml",
        "views/res_partner_job_view.xml",
        "views/credit_policy_views.xml",
        "reports/custom_report_header.xml",
    ],
    'qweb': [
        # 'static/src/xml/chatter.xml',
    ],
}
