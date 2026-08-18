import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from forgebench.policy_freeze import canonical_file_hash


ROOT = Path(__file__).resolve().parents[1]
FREEZE = (
    ROOT
    / "experiments"
    / "configs"
    / "heldout-base-generation-freeze-v1.json"
)


class HeldoutExecutionFreezeTests(unittest.TestCase):
    def test_execution_artifacts_and_dry_run_plan_are_frozen(self) -> None:
        payload = json.loads(FREEZE.read_text(encoding="utf-8"))
        unsigned = dict(payload)
        expected = unsigned.pop("content_sha256")
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(expected, "sha256:" + hashlib.sha256(encoded).hexdigest())
        for artifact in payload["artifacts"]:
            self.assertEqual(
                artifact["sha256"], canonical_file_hash(ROOT / artifact["path"])
            )

        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_heldout_base_completions.py")],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        plan = json.loads(completed.stdout)
        generation = payload["base_generation"]
        self.assertEqual(plan["content_sha256"], generation["dry_run_plan_sha256"])
        self.assertEqual(len(plan["slots"]), generation["slot_count"])
        self.assertFalse(plan["hidden_grader_available_to_runner"])


if __name__ == "__main__":
    unittest.main()
