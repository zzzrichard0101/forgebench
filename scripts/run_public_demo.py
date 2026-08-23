from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from forgebench.public_demo import format_public_demo, run_public_demo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic public ForgeBench portfolio demo."
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optionally write the public demo result as JSON.",
    )
    args = parser.parse_args()

    result = run_public_demo(ROOT)
    print(format_public_demo(result))
    if args.json_output is not None:
        destination = args.json_output.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Public JSON written: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
