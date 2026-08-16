from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceWriter:
    """Append-only JSONL event writer with monotonic sequence numbers."""

    def __init__(self, path: Path, run_id: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.run_id = run_id
        self._sequence = 0

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "schema_version": 1,
            "run_id": self.run_id,
            "sequence": self._sequence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        self._sequence += 1
        return event

