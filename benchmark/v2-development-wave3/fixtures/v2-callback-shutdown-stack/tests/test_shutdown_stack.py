import unittest

from shutdown_stack import ShutdownStack


class ShutdownStackTests(unittest.TestCase):
    def test_callbacks_run_lifo_once(self):
        seen = []
        stack = ShutdownStack()
        stack.push(seen.append, "first")
        stack.push(seen.append, "second")
        stack.close()
        stack.close()
        self.assertEqual(seen, ["second", "first"])


if __name__ == "__main__":
    unittest.main()
