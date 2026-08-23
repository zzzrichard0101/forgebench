import unittest

from subprocess_request import build_request


class SubprocessRequestTests(unittest.TestCase):
    def test_renders_argument_vector_without_shell_string(self):
        request = build_request({"argv": ["tool", "--name", "{name}"]}, {"name": "demo"}, {})
        self.assertEqual(request["argv"], ["tool", "--name", "demo"])
        self.assertEqual(request["env"], {})


if __name__ == "__main__":
    unittest.main()
