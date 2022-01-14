# -*- coding: utf-8 -*-
{
    'name' : 'Intrastat Reports',
    'category': 'Accounting/Accounting',
    'description': """
Intrastat Reports
==================

Modified Odoo account_intrastat_report by QubiQ.

The changes are the following:
------------
* Change Extended Mode to Hacienda Mode to get specific columns for Hacienda
* Add and modify columns on account_intrastat_report
* Add necessary fields on Invoice
* Generate Airport / Port codes
    """,
    'depends': ['account_reports', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/country_data.xml',
        'data/code_transaction_data.xml',
        'data/code_transport_data.xml',
        # Commodity codes are loaded as CSV due to the huge amount of records.
        'data/account.intrastat.code.csv',
        'views/account_intrastat_code_view.xml',
        'views/product_view.xml',
        'views/res_country_view.xml',
        'views/res_config_settings.xml',
        'views/account_invoice_view.xml',
        'data/account_financial_report_data.xml',
        'views/search_template_view.xml',
        'views/report_invoice.xml',
        'views/purchase_order_views.xml'
    ],
    'installable': True,
    'license': 'OEEL-1',
}
