import json
import sys
import tempfile
import unittest
from pathlib import Path

from forgebench.adaptive_verification import AdaptiveVerificationRunner
from forgebench.completion import CompletionVerifier
from forgebench.completion_risk import CompletionRiskPolicy
from forgebench.evidence_packet import build_evidence_packet
from forgebench.grader import DeterministicGrader
from forgebench.workspace import create_isolated_workspace, initialize_git_workspace


ROOT = Path(__file__).resolve().parents[1]
TASK = json.loads(
    (ROOT / "benchmark" / "tasks" / "python-plugin-boundary" / "task.json").read_text(
        encoding="utf-8"
    )
)
SEED = ROOT / "benchmark" / "fixtures" / "python-plugin-boundary"
GRADERS = ROOT / "benchmark" / "graders"


class AdaptiveVerificationRunnerTests(unittest.TestCase):
    def _make_source_workspace(self, root: Path) -> Path:
        source = create_isolated_workspace(SEED, root / "sources", "source-lite")
        initialize_git_workspace(source)
        plan = {
            "objective": "Keep plugin entrypoints inside the plugin root.",
            "steps": [
                {"action": "Resolve path", "verification": "Run tests"},
                {"action": "Inspect diff", "verification": "Check API"},
            ],
            "completion_checks": ["public tests pass"],
            "immutable_paths": ["SECURITY.md", "secret.txt", "requirements.txt"],
        }
        plan_path = source / ".forgebench" / "plan.json"
        plan_path.parent.mkdir()
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        path = source / "plugin_loader.py"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            'entrypoint = (plugin_root / manifest["entrypoint"]).resolve()\n    return entrypoint.read_text(encoding="utf-8")',
            'root = plugin_root.resolve()\n    entrypoint = (root / manifest["entrypoint"]).resolve()\n    if not entrypoint.is_relative_to(root):\n        raise ValueError("outside plugin root")\n    return entrypoint.read_text(encoding="utf-8")',
        )
        path.write_text(text, encoding="utf-8")
        return source

    def test_high_risk_replay_preserves_before_state_and_repairs_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._make_source_workspace(root)
            source_before = (source / "plugin_loader.py").read_bytes()
            invocations = 0

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                nonlocal invocations
                invocations += 1
                self.assertIn("R002_MISSING_NEGATIVE_PUBLIC_EVIDENCE", prompt)
                script = (
                    "from pathlib import Path; p=Path('plugin_loader.py'); "
                    "s=p.read_text(encoding='utf-8'); "
                    "s=s.replace('if not entrypoint.is_relative_to(root):', "
                    "'if not entrypoint.is_relative_to(root) or entrypoint.suffix != \".py\":'); "
                    "p.write_text(s, encoding='utf-8')"
                )
                return [sys.executable, "-c", script]

            runner = AdaptiveVerificationRunner(
                root / "adaptive", DeterministicGrader(GRADERS)
            )
            result = runner.run(
                task=TASK,
                seed=SEED,
                source_workspace=source,
                source_run_id="source-lite",
                command_factory=command_factory,
                evidence_mode="packet",
            )

            self.assertEqual(invocations, 1)
            self.assertTrue(result.risk_decision.escalate)
            self.assertTrue(result.attempted)
            self.assertFalse(result.grade_before.passed)
            self.assertTrue(result.grade_after.passed)
            self.assertIsNotNone(result.evidence_packet)
            self.assertTrue((result.workspace.parent / "evidence-packet.json").is_file())
            self.assertEqual((source / "plugin_loader.py").read_bytes(), source_before)
            self.assertEqual(
                (result.pre_escalation_workspace / "plugin_loader.py").read_bytes(),
                source_before,
            )
            manifest = json.loads(
                (result.workspace.parent / "adaptive-manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(manifest["task_passed_before"])
            self.assertTrue(manifest["task_passed_after"])
            self.assertEqual(manifest["evidence_mode"], "packet")

    def test_packet_is_bounded_and_excludes_hidden_task_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._make_source_workspace(root)
            completion = CompletionVerifier().verify(TASK, source, SEED)
            decision = CompletionRiskPolicy().evaluate(
                task=TASK, workspace=source, completion=completion
            )
            packet = build_evidence_packet(
                task=TASK,
                workspace=source,
                decision=decision,
                max_chars=4000,
            )
            serialized = json.dumps(packet.as_dict(), ensure_ascii=False)

            self.assertLessEqual(packet.total_chars, 4000)
            self.assertIn("plugin_loader.py", packet.changed_paths)
            self.assertIn("tests/test_plugin_loader.py", [item.path for item in packet.files])
            self.assertEqual(
                len(packet.risk["verification_requirements"]["file_type"]), 2
            )
            self.assertIn(
                "extension",
                packet.risk["verification_requirements"]["file_type"][1],
            )
            self.assertNotIn("author_metadata", serialized)
            self.assertNotIn("hidden_boundary_cases", serialized)
            secret_content = (SEED / "secret.txt").read_text(encoding="utf-8").strip()
            self.assertIn("secret.txt", serialized)
            self.assertNotIn(secret_content, serialized)

    def test_resumed_cumulative_usage_is_reported_as_turn_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self._make_source_workspace(root)

            def command_factory(prompt: str, workspace: Path) -> list[str]:
                script = (
                    "import json; from pathlib import Path; "
                    "p=Path('plugin_loader.py'); s=p.read_text(encoding='utf-8'); "
                    "s=s.replace('if not entrypoint.is_relative_to(root):', "
                    "'if not entrypoint.is_relative_to(root) or entrypoint.suffix != \".py\":'); "
                    "p.write_text(s, encoding='utf-8'); "
                    "print(json.dumps({'type':'turn.completed','usage':"
                    "{'input_tokens':110,'cached_input_tokens':105,'output_tokens':20}}))"
                )
                return [sys.executable, "-c", script]

            runner = AdaptiveVerificationRunner(
                root / "adaptive", DeterministicGrader(GRADERS)
            )
            result = runner.run(
                task=TASK,
                seed=SEED,
                source_workspace=source,
                source_run_id="source-lite",
                command_factory=command_factory,
                input_token_offset=100,
                cached_input_token_offset=100,
                output_token_offset=15,
            )
            manifest = json.loads(
                (result.workspace.parent / "adaptive-manifest.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(result.input_tokens, 10)
            self.assertEqual(result.cached_input_tokens, 5)
            self.assertEqual(result.output_tokens, 5)
            self.assertEqual(
                manifest["deep_verification"]["usage_delta"]["input_tokens"], 10
            )


if __name__ == "__main__":
    unittest.main()
