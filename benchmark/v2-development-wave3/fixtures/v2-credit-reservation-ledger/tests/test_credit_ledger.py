from decimal import Decimal
import unittest

from credit_ledger import CreditLedger


class CreditLedgerTests(unittest.TestCase):
    def test_reservation_respects_account_limit(self):
        ledger = CreditLedger({"a": Decimal("10.00")})
        self.assertTrue(ledger.reserve("a", Decimal("4.00"), "r1"))
        self.assertFalse(ledger.reserve("a", Decimal("7.00"), "r2"))


if __name__ == "__main__":
    unittest.main()
