"""Print a stable SHA-256 revision for a benchmark seed directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from forgebench.catalog import hash_seed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=Path)
    args = parser.parse_args()
    print(hash_seed(args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
