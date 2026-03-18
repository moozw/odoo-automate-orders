{
    'name': 'Orders Auto Confirm',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Auto-validate delivery/receipt and post invoice/bill on order confirmation',
    'license': 'AGPL-3',
    'author': 'Mark Dawson',
    'website': 'https://github.com/moozw/odoo-automate-orders',
    'maintainer': 'Mark Dawson',
    'depends': ['sale_management', 'purchase', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_warning_wizard.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'images': ['static/description/icon.png'],
}
