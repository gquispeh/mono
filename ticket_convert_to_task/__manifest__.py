# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Create Task from Ticket',
    'category': 'Project',
    'version': '12.0.1.0.0',
    'description': """
        Create a project task from a helpdesk ticket.
    """,
    'author': 'QubiQ',
    'website': 'http://www.qubiq.es',
    'depends': [
        'base',
        'helpdesk',
        'project',
    ],

    'data': [
        'wizards/ticket_convert2task_view.xml',
        'views/helpdesk_ticket_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
