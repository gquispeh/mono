# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Create Ticket from Lead',
    'category': 'CRM',
    'version': '12.0.1.0.0',
    'description': """
        Create a helpdesk ticket from a CRM lead.
    """,
    'author': 'QubiQ',
    'website': 'http://www.qubiq.es',
    'depends': [
        'base',
        'crm',
        'helpdesk',
    ],

    'data': [
        'wizards/crm_lead_convert2ticket_view.xml',
        'views/crm_lead_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
