import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']  # list form — forward-compatible with Odoo 19

    def button_confirm(self):
        """Override to auto-validate the receipt and post a vendor bill when
        the company has ``auto_confirm_purchase`` enabled in Purchase settings.

        Flow when feature is ON:
          1. super().button_confirm()  ← creates the receipt picking
          2. _validate_receipts()      ← sets qty_done = demand, validates
          3. _create_and_post_bills()  ← creates bill, sets invoice_date=today,
                                         posts it

        The invoice_date write uses check_move_validity=False to avoid the
        intermediate balance-validation error that causes automated actions to
        fail when writing directly to a freshly created draft vendor bill.
        """
        if not self.env.company.auto_confirm_purchase:
            return super().button_confirm()

        result = super().button_confirm()

        for order in self:
            order._validate_receipts()
            try:
                order._create_and_post_bills()
            except Exception:
                _logger.exception(
                    'orders_auto_confirm: bill creation failed for PO %s — '
                    'receipt was validated; create the bill manually.',
                    order.name,
                )

        return result

    # ------------------------------------------------------------------
    # Private helpers — each operates on a single order (ensure_one).
    # ------------------------------------------------------------------

    def _validate_receipts(self):
        """Validate all incoming receipts for this purchase order.

        For incoming pickings Odoo does not reserve stock, so qty_done is 0
        by default. We explicitly set qty_done = product_uom_qty on every move
        before calling button_validate — otherwise the "Immediate Transfer"
        wizard fires and blocks automation.
        """
        self.ensure_one()
        receipts = self.picking_ids.filtered(
            lambda p: p.state not in ('done', 'cancel')
        )
        for picking in receipts:
            if picking.state == 'draft':
                picking.action_confirm()

            # Pre-fill done quantities so button_validate does not open the
            # Immediate Transfer wizard.
            # Odoo 17+ renamed quantity_done → quantity on stock.move.
            for move in picking.move_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
            ):
                move.quantity = move.product_uom_qty

            result = picking.with_context(skip_backorder=True).button_validate()
            if isinstance(result, dict):
                _logger.warning(
                    'orders_auto_confirm: receipt %s returned an action from '
                    'button_validate (state=%s). Forcing _action_done.',
                    picking.name, picking.state,
                )
                if picking.state not in ('done', 'cancel'):
                    picking._action_done()

    def _create_and_post_bills(self):
        """Create a vendor bill for this PO, set today as the bill date, post it.

        Why check_move_validity=False when writing invoice_date:
        account.move runs _check_balanced() after every write on a draft move.
        On a freshly created bill the journal items are not yet balanced (Odoo
        finalises them on post), so writing invoice_date triggers a spurious
        validation error.  Suppressing that intermediate check and letting
        action_post() do the final validation is the correct approach — this
        is exactly what the standard Odoo UI does through onchange, but onchange
        is not called in server-side code.
        """
        self.ensure_one()

        # Capture existing bill IDs so we can identify what was just created.
        existing_bill_ids = set(self.invoice_ids.ids)

        # action_create_invoice() handles grouping, line preparation, and
        # linking; we call it for its side-effects and ignore the returned
        # action dict.
        self.action_create_invoice()

        new_bills = self.invoice_ids.filtered(
            lambda m: m.id not in existing_bill_ids
        )
        if not new_bills:
            _logger.warning(
                'orders_auto_confirm: no bill created for PO %s', self.name
            )
            return

        # Write invoice_date bypassing intermediate balance validation.
        # This is the key fix for the failure seen with automated actions.
        new_bills.with_context(check_move_validity=False).write({
            'invoice_date': fields.Date.today(),
        })
        new_bills.action_post()
