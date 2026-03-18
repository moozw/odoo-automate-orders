from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']
    _description = 'Settings'

    auto_confirm_sale = fields.Boolean(
        related='company_id.auto_confirm_sale',
        readonly=False,
        string='Auto-confirm delivery & invoice on sale confirmation',
    )
    auto_confirm_purchase = fields.Boolean(
        related='company_id.auto_confirm_purchase',
        readonly=False,
        string='Auto-confirm receipt & bill on purchase order confirmation',
    )
