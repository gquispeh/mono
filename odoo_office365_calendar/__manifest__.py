# See LICENSE file for full copyright and licensing details.

{
    'name': 'ODOO - Office365 Calendar Integration',
    'version': '12.0.1.0.0',
    'category': 'Calendar',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'summary': """
        Single sign on with microsoft SSO microsoft Office 365 login with odoo
        office 365 sso odoo microsoft integration office 365 calendar and
        contact synchronization office 365 synchronization office 365
    """,
    'depends': ['odoo_microsoft_account', 'calendar'],
    'qweb': ['static/src/xml/*.xml'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/office365_calendar_data.xml',
        'views/o365_calendar.xml',
    ],
    'images': ['static/description/banner01.png'],
    'installable': True,
    'auto_install': False,
    'price': 250,
    'currency': 'EUR'
}
