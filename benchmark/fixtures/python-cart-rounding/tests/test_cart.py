import unittest
from decimal import Decimal

from cart import invoice_total, line_total


class CartTests(unittest.TestCase):
    def test_line_total_is_money(self) -> None:
        self.assertEqual(line_total(2, Decimal("1.25")), Decimal("2.50"))

    def test_invoice_total_for_exact_prices(self) -> None:
        items = [(2, Decimal("1.25")), (1, Decimal("3.50"))]
        self.assertEqual(invoice_total(items), Decimal("6.00"))


if __name__ == "__main__":
    unittest.main()

