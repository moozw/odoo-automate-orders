from odoo import fields, models


class SaleStockWarningWizard(models.TransientModel):
    """Blocking popup shown when a sale order cannot be auto-confirmed due to
    insufficient on-hand stock.  The only action available to the user is
    closing the wizard — no bypass is provided.
    """

    _name = 'orders.stock.warning.wizard'
    _description = 'Sale Order Insufficient Stock Warning'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        readonly=True,
    )
    warning_lines = fields.Text(
        string='Insufficient Stock Details',
        readonly=True,
    )

    def action_close(self):
        """Close the wizard. The sale order remains in draft."""
        return {'type': 'ir.actions.act_window_close'}
