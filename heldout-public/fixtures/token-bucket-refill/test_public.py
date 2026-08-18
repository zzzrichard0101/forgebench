import unittest

from token_bucket import TokenBucket


class TokenBucketTests(unittest.TestCase):
    def test_full_bucket_allows_capacity(self):
        bucket = TokenBucket(2, 1, 0)
        self.assertTrue(bucket.allow(0))
        self.assertTrue(bucket.allow(0))
        self.assertFalse(bucket.allow(0))


if __name__ == "__main__":
    unittest.main()
