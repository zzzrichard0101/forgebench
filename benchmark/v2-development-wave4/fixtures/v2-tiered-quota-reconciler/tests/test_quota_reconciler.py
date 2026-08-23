import unittest
from decimal import Decimal
from quota_reconciler import allocate_quota

class PublicTests(unittest.TestCase):
    def test_allocates(self):
        result = allocate_quota(Decimal("2.00"), [{"id": "a", "tier": "gold", "amount": Decimal("1.00")}], {"gold": Decimal("2.00")})
        self.assertEqual(result["allocations"]["a"], Decimal("1.00"))

if __name__ == "__main__": unittest.main()
