import json
import unittest

from forgebench.codex_model import (
    CodexModelError,
    parse_codex_jsonl,
    parse_model_action,
)


class CodexModelAdapterTests(unittest.TestCase):
    def test_tool_action_is_parsed(self) -> None:
        action = parse_model_action(
            '{"kind":"tool","tool_call":{"name":"read_file","arguments":{"path":"source.json"}}}'
        )
        self.assertEqual(action.kind, "tool")
        self.assertEqual(action.tool_call.name, "read_file")

    def test_fenced_finish_action_is_parsed(self) -> None:
        action = parse_model_action(
            '```json\n{"kind":"finish","final_answer":"done"}\n```'
        )
        self.assertEqual(action.kind, "finish")
        self.assertEqual(action.final_answer, "done")

    def test_single_example_wrapper_is_tolerated(self) -> None:
        action = parse_model_action(
            '{"tool_action":{"kind":"tool","tool_call":{"name":"read_file","arguments":{"path":"source.json"}}}}'
        )
        self.assertEqual(action.tool_call.name, "read_file")

    def test_invalid_action_is_rejected(self) -> None:
        with self.assertRaises(CodexModelError):
            parse_model_action('{"kind":"tool","tool_call":{"name":7}}')

    def test_last_agent_message_and_usage_are_selected(self) -> None:
        events = [
            {"type":"item.completed","item":{"type":"agent_message","text":"first"}},
            {"type":"item.completed","item":{"type":"agent_message","text":'{"kind":"finish","final_answer":"done"}'}},
            {"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3}}
        ]
        message, usage = parse_codex_jsonl(
            "\n".join(json.dumps(event) for event in events)
        )
        self.assertIn('"finish"', message)
        self.assertEqual(usage["input_tokens"], 12)


if __name__ == "__main__":
    unittest.main()
