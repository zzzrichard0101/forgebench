"""Validate the V2 public corpus and, optionally, its separate oracle catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.v2_corpus import audit_v2_labeled_corpus, validate_v2_public_corpus


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--oracle-catalog", type=Path)
    parser.add_argument(
        "--exclude-manifest",
        type=Path,
        action="append",
        default=[],
        help="V1 manifest whose task IDs and seed revisions are forbidden",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    exclusions = args.exclude_manifest or [
        ROOT / "benchmark" / "manifest.json",
        ROOT / "heldout-public" / "manifest.json",
    ]
    public = validate_v2_public_corpus(
        public_root=args.public_root,
        manifest_path=args.manifest,
        repository_root=ROOT,
        exclusion_manifest_paths=exclusions,
    )
    if args.oracle_catalog is None:
        result = {
            "schema_version": 1,
            "status": "public_corpus_valid",
            "snapshot": public.payload["snapshot"],
            "frozen": public.payload["frozen"],
            "case_count": len(public.payload["cases"]),
            "public_manifest_sha256": public.content_sha256,
        }
    else:
        result = audit_v2_labeled_corpus(
            public, oracle_catalog_path=args.oracle_catalog
        ).as_dict()
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
