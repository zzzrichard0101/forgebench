import unittest

from forgebench.codex_command import build_exec_command, build_resume_command


class CodexCommandTests(unittest.TestCase):
    def test_persisted_exec_omits_ephemeral_flag(self) -> None:
        command = build_exec_command(
            prefix=["codex"],
            prompt="do work",
            workspace="C:/work",
            model="model",
            reasoning_effort="medium",
            persist_session=True,
        )

        self.assertNotIn("--ephemeral", command)
        self.assertEqual(command[-1], "do work")

    def test_ephemeral_exec_retains_historical_default(self) -> None:
        command = build_exec_command(
            prefix=["codex"],
            prompt="do work",
            workspace="C:/work",
            model="model",
            reasoning_effort="medium",
            persist_session=False,
        )

        self.assertIn("--ephemeral", command)

    def test_resume_uses_explicit_workspace_and_session(self) -> None:
        command = build_resume_command(
            prefix=["codex"],
            session_id="session-123",
            prompt="verify",
            workspace="C:/isolated",
            model="model",
            reasoning_effort="medium",
        )

        self.assertEqual(command[command.index("--cd") + 1], "C:/isolated")
        self.assertEqual(command[command.index("resume") + 1], "--json")
        self.assertEqual(command[-2:], ["session-123", "verify"])
        self.assertNotIn("--ephemeral", command)


if __name__ == "__main__":
    unittest.main()
