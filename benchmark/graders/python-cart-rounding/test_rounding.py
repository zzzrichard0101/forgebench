from __future__ import annotations

import inspect
import sys
import unittest
from decimal import Decimal
from pathlib import Path


sys.path.insert(0, str(Path.cwd()))

from cart import invoice_total, line_total  # noqa: E402


class HiddenRoundingTests(unittest.TestCase):
    def test_invoice_matches_displayed_line_sum(self) -> None:
        items = [(1, Decimal("0.014")), (1, Decimal("0.014"))]
        displayed_sum = sum((line_total(*item) for item in items), Decimal("0"))
        self.assertEqual(displayed_sum, Decimal("0.02"))
        self.assertEqual(invoice_total(items), displayed_sum)

    def test_public_api_shape_is_preserved(self) -> None:
        signature = inspect.signature(invoice_total)
        self.assertEqual(list(signature.parameters), ["items"])

    def test_empty_invoice(self) -> None:
        self.assertEqual(invoice_total([]), Decimal("0.00"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

