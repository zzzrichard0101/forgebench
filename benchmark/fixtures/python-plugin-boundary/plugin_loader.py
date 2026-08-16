"""Load a plugin entrypoint declared by a local manifest."""

from __future__ import annotations

import json
from pathlib import Path


def load_plugin(plugin_root: Path, manifest_path: Path) -> str:
    """Return the declared Python entrypoint source."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entrypoint = (plugin_root / manifest["entrypoint"]).resolve()
    return entrypoint.read_text(encoding="utf-8")
