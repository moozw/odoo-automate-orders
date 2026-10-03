"""What happens when the automation validates the receipt but the bill fails.

The automation deliberately continues after a business error from bill
creation, so that a goods receipt is never blocked by an accounting problem.
That choice is only safe if the failed bill work is rolled back: bill creation
and posting are several writes, and without a savepoint a bill created and then
rejected at posting stayed behind as a half-made draft, committed alongside the
receipt, with only a server log to say so.
"""

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseBillFailure(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.auto_confirm_purchase = True
        cls.vendor = cls.env['res.partner'].create({
            'name': 'OAC Bill Failure Vendor', 'supplier_rank': 1,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'OAC Bill Failure Product',
            'is_storable': True,
            'list_price': 10.0,
            'standard_price': 5.0,
        })

    def _order(self, qty=2.0):
        return self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': qty,
                'product_uom': self.product.uom_id.id,
                'price_unit': 5.0,
                'date_planned': self.env.cr.now(),
            })],
        })

    def test_a_successful_confirm_receives_and_bills(self):
        """The ordinary path, so the tests below are about failure only."""
        order = self._order()
        order.button_confirm()
        self.assertEqual(order.state, 'purchase')
        self.assertTrue(
            order.picking_ids.filtered(lambda p: p.state == 'done'),
            'the receipt should be validated',
        )
        self.assertTrue(order.invoice_ids, 'a bill should have been created')

    def test_a_failed_bill_leaves_no_partial_draft_behind(self):
        """Create a bill, then fail: the savepoint must undo the bill."""
        order = self._order()
        real = type(order)._create_and_post_bills

        def create_then_fail(self_order):
            real(self_order)  # really creates the bill
            raise UserError('Simulated posting failure')

        with patch.object(
            type(order), '_create_and_post_bills', create_then_fail,
        ):
            order.button_confirm()

        self.assertEqual(
            order.state, 'purchase',
            'the order must still be confirmed - the goods arrived',
        )
        self.assertTrue(
            order.picking_ids.filtered(lambda p: p.state == 'done'),
            'the receipt must stay validated; a warehouse user is not blocked '
            'by an accounting problem',
        )
        self.assertFalse(
            order.invoice_ids,
            'the bill work must be rolled back, leaving no half-made draft',
        )

    def test_a_failed_bill_is_reported_on_the_order(self):
        """A server log is invisible to whoever pressed Confirm."""
        order = self._order()

        def just_fail(self_order):
            raise UserError('Simulated posting failure')

        with patch.object(type(order), '_create_and_post_bills', just_fail):
            order.button_confirm()

        self.assertTrue(
            order.message_ids.filtered(
                lambda m: 'vendor bill could not be created' in (m.body or '')
            ),
            'the failure must be recorded on the order for somebody to action',
        )
