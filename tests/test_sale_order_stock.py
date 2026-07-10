from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderStockAvailability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Orders Auto Confirm Test Customer',
        })
        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.product = cls.env['product.product'].create({
            'name': 'Orders Auto Confirm Test Product',
            'is_storable': True,
            'list_price': 10.0,
            'standard_price': 5.0,
        })

    def _set_stock(self, quantity):
        self.env['stock.quant']._update_available_quantity(
            self.product,
            self.warehouse.lot_stock_id,
            quantity,
        )

    def _create_order(self, quantities):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': quantity,
                    'price_unit': self.product.list_price,
                })
                for quantity in quantities
            ],
        })

    def test_duplicate_lines_are_checked_in_aggregate(self):
        self._set_stock(4)
        order = self._create_order([3, 3])

        insufficient = order._check_stock_availability()

        self.assertEqual(len(insufficient), 1)
        self.assertEqual(insufficient[0]['product'], self.product.display_name)
        self.assertEqual(insufficient[0]['required'], 6.0)
        self.assertEqual(insufficient[0]['available'], 4.0)

    def test_duplicate_lines_pass_when_total_is_available(self):
        self._set_stock(4)
        order = self._create_order([2, 2])

        insufficient = order._check_stock_availability()

        self.assertFalse(insufficient)
