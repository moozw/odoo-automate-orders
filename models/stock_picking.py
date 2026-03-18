import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = ['stock.picking']
    _description = 'Stock Picking'

    def _auto_force_validate(self):
        """Pre-fill done quantities and force-validate this picking.

        Sets ``move.quantity = move.product_uom_qty`` on all active moves so
        that ``button_validate`` does not open the Immediate Transfer wizard.
        Uses ``skip_backorder=True`` to suppress the backorder popup.

        If ``button_validate`` returns an action dict instead of ``True``
        (which should not happen after quantities are pre-filled), the method
        logs a warning and calls ``_action_done`` directly.

        Called by both ``sale.order._confirm_pickings`` and
        ``purchase.order._validate_receipts``.
        """
        self.ensure_one()
        for move in self.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.quantity = move.product_uom_qty

        result = self.with_context(skip_backorder=True).button_validate()
        if isinstance(result, dict):
            _logger.warning(
                'orders_auto_confirm: picking %s returned an action from '
                'button_validate (state=%s). Forcing _action_done.',
                self.name, self.state,
            )
            if self.state not in ('done', 'cancel'):
                self._action_done()
