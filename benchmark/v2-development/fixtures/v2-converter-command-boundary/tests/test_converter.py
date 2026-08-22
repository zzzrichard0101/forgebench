import unittest

from converter import build_command


class ConverterTests(unittest.TestCase):
    def test_regular_operands_remain_separate(self):
        self.assertEqual(
            build_command("input.png", "output.webp"),
            ["imgconvert", "input.png", "output.webp"],
        )


if __name__ == "__main__":
    unittest.main()

