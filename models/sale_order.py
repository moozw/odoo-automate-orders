import logging

from odoo import _, fields, models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = ['sale.order']  # list form — forward-compatible with Odoo 19
    _description = 'Sale Order'

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

        Skips non-storable products. In Odoo 17+ storable goods have
        ``is_storable = True``; consumables and services do not.
        Returns an empty list when all lines are OK.
        """
        self.ensure_one()
        insufficient = []
        # Odoo 17+: storable goods have type='consu' with is_storable=True.
        # Consumables (untracked) also have type='consu' but is_storable=False.
        # Only storable products carry tracked inventory — skip everything else.
        storable_lines = self.order_line.filtered(lambda l: l.product_id.is_storable)
        if not storable_lines:
            return insufficient

        # Batch-fetch free_qty for all storable products in one context switch.
        # Calling with_context() on the full recordset (rather than per-line) lets
        # Odoo prefetch the underlying stock.quant queries in a single round-trip.
        products = storable_lines.product_id.with_context(warehouse=self.warehouse_id.id)
        products.read(['free_qty'])  # force batch computation
        free_qty_map = {p.id: p.free_qty for p in products}

        for line in storable_lines:
            available = free_qty_map[line.product_id.id]
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
            # action_assign only needed for outgoing pickings in confirmed state;
            # already-assigned pickings skip this safely.
            if picking.state == 'confirmed':
                picking.action_assign()
            picking._auto_force_validate()

    def _create_and_post_invoices(self):
        """Create an invoice for this order, set today's date, and post it."""
        self.ensure_one()
        invoices = self._create_invoices()
        if not invoices:
            _logger.warning(
                'orders_auto_confirm: no invoice created for order %s', self.name
            )
            return
        # WARNING: do not add fields to this write() dict without re-evaluating
        # check_move_validity=False — that context key bypasses balance validation.
        invoices.with_context(check_move_validity=False).write({'invoice_date': fields.Date.today()})
        invoices.action_post()
