import tempfile
import unittest
from pathlib import Path

from sandbox_path import SandboxPathMapper


class SandboxPathMapperTests(unittest.TestCase):
    def test_maps_simple_relative_path(self):
        with tempfile.TemporaryDirectory() as temp:
            mapper = SandboxPathMapper(temp)
            self.assertEqual(mapper.resolve("assets/icon.png"), Path(temp) / "assets" / "icon.png")


if __name__ == "__main__":
    unittest.main()
