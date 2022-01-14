# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Monolitic CRM Project",

    'summary': """
        Link CRM Opportunities with Projects
    """,

    'description': """
        Create Projects from Opportunities
    """,

    'author': "QubiQ",
    'website': "https://www.qubiq.es",
    'category': 'CRM',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['crm', 'project'],
    "data": [
        'views/crm_lead_views.xml',
        'views/project_views.xml',
    ],
    'installable': True,
    'application': False,
}
