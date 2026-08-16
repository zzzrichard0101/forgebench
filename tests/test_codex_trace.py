import json
import tempfile
import unittest
from pathlib import Path

from forgebench.codex_trace import summarize_codex_trace


class CodexTraceTests(unittest.TestCase):
    def test_trace_summary_and_budget_qualification(self) -> None:
        events = [
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "status": "failed"},
            },
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "status": "completed"},
            },
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 120,
                    "cached_input_tokens": 80,
                    "output_tokens": 30,
                    "reasoning_output_tokens": 10,
                },
            },
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "trace.jsonl"
            path.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            summary = summarize_codex_trace(path)

        self.assertEqual(summary.event_count, 4)
        self.assertEqual(summary.command_count, 2)
        self.assertEqual(summary.command_completed, 1)
        self.assertEqual(summary.command_failed, 1)
        self.assertTrue(
            summary.budget_compliant(
                {"max_input_tokens": 120, "max_output_tokens": 30}
            )
        )
        self.assertFalse(
            summary.budget_compliant(
                {"max_input_tokens": 119, "max_output_tokens": 30}
            )
        )

    def test_invalid_jsonl_reports_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "trace.jsonl"
            path.write_text('{}\n{"broken"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2"):
                summarize_codex_trace(path)


if __name__ == "__main__":
    unittest.main()
