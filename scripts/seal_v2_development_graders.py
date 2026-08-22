"""Seal repair-development graders without claiming independent custody."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from forgebench.policy_freeze import canonical_file_hash
from forgebench.v2_corpus import payload_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grader-root", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    grader_root = args.grader_root.resolve(strict=True)
    audit_path = args.audit.resolve(strict=True)
    output = args.output.resolve(strict=False)
    if output == grader_root or output.is_relative_to(grader_root):
        raise ValueError("seal output must be outside the grader root")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "passed" or audit.get("repetitions", 0) < 3:
        raise ValueError("a passing three-repeat grader audit is required")
    audited_ids = {record["task_id"] for record in audit.get("tasks", [])}
    actual_ids = {path.name for path in grader_root.iterdir() if path.is_dir()}
    if not audited_ids or audited_ids != actual_ids:
        raise ValueError("grader directories do not match the audit")
    records = []
    for task_id in sorted(actual_ids):
        task_root = grader_root / task_id
        files = sorted(path for path in task_root.rglob("*") if path.is_file())
        if not files:
            raise ValueError(f"grader directory is empty: {task_id}")
        digest = hashlib.sha256()
        for path in files:
            relative = path.relative_to(task_root).as_posix().encode("utf-8")
            file_hash = canonical_file_hash(path).encode("ascii")
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(file_hash)
        records.append(
            {"task_id": task_id, "grader_sha256": "sha256:" + digest.hexdigest()}
        )
    payload = {
        "schema_version": 1,
        "seal_version": "v2-development-grader-seal-v1",
        "split": "repair_dev",
        "development_only": True,
        "independent_custodian": False,
        "eligible_for_mechanism_validation": False,
        "audit_sha256": canonical_file_hash(audit_path),
        "task_graders": records,
    }
    payload["content_sha256"] = payload_hash(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
