import unittest

from stream_redactor import StreamRedactor


class StreamRedactorTests(unittest.TestCase):
    def test_secret_inside_one_chunk(self):
        redactor = StreamRedactor(["TOKEN"])
        self.assertEqual(redactor.feed("a TOKEN b") + redactor.finish(), "a [REDACTED] b")


if __name__ == "__main__":
    unittest.main()

