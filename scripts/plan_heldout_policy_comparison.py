"""Freeze held-out policy assignments from public sealed bases only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.base_completion import BaseCompletionStore
from forgebench.catalog import BenchmarkCatalog
from forgebench.comparison_manifest import (
    ComparisonCandidate,
    ComparisonManifestPlanner,
)
from forgebench.public_base_discovery import discover_public_base_entries
from run_codex_baseline import ROOT


HELDOUT_MANIFEST = ROOT / "heldout-public" / "manifest.json"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "heldout-v1"
DEFAULT_BASE_ROOT = DEFAULT_RUNS_ROOT / "base-completions-attempt-2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-id", required=True)
    parser.add_argument("--random-seed", type=int, required=True)
    parser.add_argument("--task-manifest", type=Path, default=HELDOUT_MANIFEST)
    parser.add_argument("--base-root", type=Path, default=DEFAULT_BASE_ROOT)
    parser.add_argument(
        "--routing-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT / "assignment-routing",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RUNS_ROOT / "comparison-manifests" / "heldout-v1.json",
    )
    args = parser.parse_args()

    catalog = BenchmarkCatalog(ROOT, args.task_manifest)
    store = BaseCompletionStore(args.base_root)
    entries = discover_public_base_entries(args.base_root)
    candidates = [
        ComparisonCandidate(store.load(base_id), catalog.get(task_id).task)
        for task_id, base_id in entries
    ]
    manifest = ComparisonManifestPlanner(args.routing_root).plan(
        candidates=candidates,
        output_path=args.output,
        random_seed=args.random_seed,
        manifest_id=args.manifest_id,
    )
    print(
        json.dumps(
            {
                "schema_version": 1,
                "manifest_id": manifest.manifest_id,
                "content_sha256": manifest.content_sha256,
                "base_count": len(manifest.payload["bases"]),
                "task_manifest": str(args.task_manifest),
                "strata": manifest.payload["strata"],
                "hidden_labels_read": False,
                "path": str(manifest.path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
