from odoo import fields, models


class ResCompany(models.Model):
    _inherit = ['res.company']
    _description = 'Company'

    auto_confirm_sale = fields.Boolean(
        string='Auto-confirm delivery & invoice on sale confirmation',
        default=False,
    )
    auto_confirm_purchase = fields.Boolean(
        string='Auto-confirm receipt & bill on purchase order confirmation',
        default=False,
    )
