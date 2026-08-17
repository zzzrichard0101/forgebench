import tempfile
import unittest
from pathlib import Path

from forgebench.model_recovery import FirstReadTimeoutGateway, grade_recovery_workspace
from forgebench.tools import ToolGateway
from forgebench.types import ToolCall


class ModelRecoveryTests(unittest.TestCase):
    def test_only_first_target_read_is_injected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            (workspace / "source.json").write_text('{"ok":true}\n', encoding="utf-8")
            gateway = FirstReadTimeoutGateway(ToolGateway(workspace))
            call = ToolCall("read_file", {"path":"source.json"})
            first = gateway.execute(call)
            second = gateway.execute(call)
        self.assertFalse(first.ok)
        self.assertEqual(first.metadata["error_kind"], "timeout")
        self.assertTrue(second.ok)

    def test_grade_requires_exact_json_and_unchanged_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / "seed"
            workspace = root / "workspace"
            seed.mkdir()
            workspace.mkdir()
            for target in (seed, workspace):
                (target / "source.json").write_text('{"ok":true}\n', encoding="utf-8")
            (workspace / "result.json").write_text('{"ok": true}\n', encoding="utf-8")
            grade = grade_recovery_workspace(workspace, seed)
        self.assertTrue(grade["task_passed"])


if __name__ == "__main__":
    unittest.main()
