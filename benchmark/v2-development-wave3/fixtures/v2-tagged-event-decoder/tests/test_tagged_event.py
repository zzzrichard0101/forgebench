import unittest

from tagged_event import decode_event


class TaggedEventTests(unittest.TestCase):
    def test_decodes_created_event(self):
        payload = {
            "version": 1,
            "kind": "created",
            "id": "e1",
            "data": {"name": "demo"},
        }
        result = decode_event(payload)
        self.assertEqual(result["kind"], "created")
        self.assertEqual(result["id"], "e1")
        self.assertEqual(result["data"], {"name": "demo"})


if __name__ == "__main__":
    unittest.main()
