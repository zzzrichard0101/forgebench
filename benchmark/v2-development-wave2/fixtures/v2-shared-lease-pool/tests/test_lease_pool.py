import unittest

from lease_pool import LeasePool


class LeasePoolTests(unittest.TestCase):
    def test_single_lease_releases(self):
        events = []
        pool = LeasePool(lambda key: events.append(("acquire", key)) or object(), lambda resource: events.append(("release", resource)))
        with pool.lease("db"):
            pass
        self.assertEqual([event[0] for event in events], ["acquire", "release"])


if __name__ == "__main__":
    unittest.main()

