"""Validate public held-out assets without accepting a private grader path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forgebench.heldout_intake import validate_heldout_intake


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-root", type=Path, default=ROOT)
    parser.add_argument("--heldout-manifest", type=Path, required=True)
    parser.add_argument(
        "--development-manifest",
        type=Path,
        default=ROOT / "benchmark" / "manifest.json",
    )
    parser.add_argument("--private-seal", type=Path, required=True)
    parser.add_argument(
        "--policy-freeze",
        type=Path,
        default=(
            ROOT
            / "experiments"
            / "configs"
            / "selective-verification-policy-freeze-v1.json"
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_heldout_intake(
        public_root=args.public_root,
        heldout_manifest_path=args.heldout_manifest,
        development_manifest_path=args.development_manifest,
        private_seal_path=args.private_seal,
        policy_freeze_path=args.policy_freeze,
        policy_repository_root=ROOT,
    ).as_dict()
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
