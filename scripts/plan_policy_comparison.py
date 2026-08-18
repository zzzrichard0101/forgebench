"""Freeze public-only policy assignments across multiple base completions."""

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
from run_codex_baseline import MANIFEST_PATH, ROOT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--entry",
        action="append",
        required=True,
        metavar="TASK_ID=BASE_ID",
        help="Repeat once per sealed base completion.",
    )
    parser.add_argument("--manifest-id", required=True)
    parser.add_argument("--random-seed", type=int, required=True)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--routing-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    catalog = BenchmarkCatalog(ROOT, MANIFEST_PATH)
    base_root = args.base_root or (args.runs_root / "base-completions")
    store = BaseCompletionStore(base_root)
    candidates: list[ComparisonCandidate] = []
    for raw in args.entry:
        if "=" not in raw:
            raise ValueError("--entry must use TASK_ID=BASE_ID")
        task_id, base_id = raw.split("=", 1)
        bundle = catalog.get(task_id)
        candidates.append(ComparisonCandidate(store.load(base_id), bundle.task))

    output_path = args.output or (
        args.runs_root / "comparison-manifests" / f"{args.manifest_id}.json"
    )
    routing_root = args.routing_root or (args.runs_root / "assignment-routing")
    manifest = ComparisonManifestPlanner(routing_root).plan(
        candidates=candidates,
        output_path=output_path,
        random_seed=args.random_seed,
        manifest_id=args.manifest_id,
    )
    output = {
        "schema_version": 1,
        "manifest_id": manifest.manifest_id,
        "content_sha256": manifest.content_sha256,
        "base_count": len(manifest.payload["bases"]),
        "strata": manifest.payload["strata"],
        "path": str(manifest.path),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
