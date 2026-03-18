import logging

from odoo import _, fields, models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = ['sale.order']  # list form — forward-compatible with Odoo 19

    def action_confirm(self):
        """Override to auto-validate delivery and post invoice when the
        company has ``auto_confirm_sale`` enabled in Sales settings.

        Flow when feature is ON and len(self) == 1:
          1. Check stock availability for all storable lines.
          2. If insufficient → open blocking wizard (order stays draft).
          3. If sufficient → super().action_confirm(), validate pickings,
             create + post invoice dated today.

        For bulk confirms (len(self) > 1), delegate entirely to standard Odoo
        so that draft pickings are created normally with no auto-validation.
        """
        if not self.env.company.auto_confirm_sale:
            return super().action_confirm()

        if len(self) > 1:
            # Bulk confirm: standard Odoo behaviour — draft pickings only, no automation.
            return super().action_confirm()

        # Single order: stock check → wizard or full auto-validate.
        insufficient = self._check_stock_availability()
        if insufficient:
            warning_lines = '\n'.join(
                "• {product}: need {required:.2f}, available {available:.2f}".format(**item)
                for item in insufficient
            )
            wizard = self.env['orders.stock.warning.wizard'].create({
                'sale_order_id': self.id,
                'warning_lines': warning_lines,
            })
            return {
                'name': _('Insufficient Stock'),
                'type': 'ir.actions.act_window',
                'res_model': 'orders.stock.warning.wizard',
                'res_id': wizard.id,
                'view_mode': 'form',
                'target': 'new',
            }

        result = super().action_confirm()
        self._confirm_pickings()
        self._create_and_post_invoices()
        return result

    # ------------------------------------------------------------------
    # Private helpers — each operates on a single order (ensure_one).
    # ------------------------------------------------------------------

    def _check_stock_availability(self):
        """Return a list of dicts for lines with insufficient on-hand stock.

        Skips service/consumable products (only storable products with
        ``type == 'product'`` carry inventory).
        Returns an empty list when all lines are OK.
        """
        self.ensure_one()
        insufficient = []
        for line in self.order_line:
            if line.product_id.type != 'product':
                continue
            available = line.product_id.with_context(
                warehouse=self.warehouse_id.id
            ).free_qty
            required = line.product_uom_qty
            if float_compare(available, required, precision_rounding=line.product_uom.rounding) < 0:
                insufficient.append({
                    'product': line.product_id.display_name,
                    'required': required,
                    'available': available,
                })
        return insufficient

    def _confirm_pickings(self):
        """Confirm, assign, and immediately validate all outgoing pickings.

        Uses ``skip_backorder=True`` context so no backorder wizard appears.
        If ``button_validate`` returns an action dict (e.g. immediate transfer
        wizard) instead of True, we log a warning and fall back to
        ``_action_done`` to force completion.
        """
        self.ensure_one()
        pickings = self.picking_ids.filtered(
            lambda p: p.state not in ('done', 'cancel')
        )
        for picking in pickings:
            if picking.state == 'draft':
                picking.action_confirm()
            picking.action_assign()

            # Pre-fill done quantities so button_validate does not open the
            # Immediate Transfer wizard (which would return a dict and leave
            # the picking unvalidated or force _action_done with 0 qty).
            # Mirrors the pattern used in _validate_receipts() in purchase_order.py.
            for move in picking.move_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
            ):
                move.quantity = move.product_uom_qty

            # skip_backorder avoids the "Create Backorder?" popup.
            result = picking.with_context(skip_backorder=True).button_validate()
            if isinstance(result, dict):
                # Shouldn't happen after a passing stock check, but log it.
                _logger.warning(
                    'orders_auto_confirm: picking %s returned an action from '
                    'button_validate (state=%s). Forcing _action_done.',
                    picking.name, picking.state,
                )
                if picking.state not in ('done', 'cancel'):
                    picking._action_done()

    def _create_and_post_invoices(self):
        """Create an invoice for this order, set today's date, and post it."""
        self.ensure_one()
        invoices = self._create_invoices()
        if not invoices:
            _logger.warning(
                'orders_auto_confirm: no invoice created for order %s', self.name
            )
            return
        invoices.with_context(check_move_validity=False).write({'invoice_date': fields.Date.today()})
        invoices.action_post()
