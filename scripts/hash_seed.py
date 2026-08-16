"""Print a stable SHA-256 revision for a benchmark seed directory."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache"}


def hash_seed(root: Path) -> str:
    root = root.resolve(strict=True)
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not (set(path.relative_to(root).parts) & IGNORED_PARTS)
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=Path)
    args = parser.parse_args()
    print(hash_seed(args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
