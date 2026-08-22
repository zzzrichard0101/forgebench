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
    / "heldout-model-policy-replay-freeze-v1.json"
)


class HeldoutModelReplayFreezeTests(unittest.TestCase):
    def test_model_replay_plan_and_artifacts_are_frozen(self) -> None:
        freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
        unsigned = dict(freeze)
        expected = unsigned.pop("content_sha256")
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(expected, "sha256:" + hashlib.sha256(encoded).hexdigest())
        for artifact in freeze["artifacts"]:
            self.assertEqual(
                artifact["sha256"], canonical_file_hash(ROOT / artifact["path"])
            )

        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_heldout_model_policy_batch.py")],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        plan = json.loads(completed.stdout)
        self.assertEqual(plan["content_sha256"], freeze["plan_sha256"])
        self.assertEqual(plan["slot_count"], 120)
        self.assertEqual(plan["expected_model_calls"], 57)
        self.assertEqual(plan["expected_probe_calls"], 9)
        self.assertFalse(plan["private_grader_available"])


if __name__ == "__main__":
    unittest.main()
