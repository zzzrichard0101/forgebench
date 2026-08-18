from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FREEZE_VERSION = "selective-verification-policy-freeze-v1"


@dataclass(frozen=True)
class PolicyFreeze:
    path: Path
    payload: dict[str, Any]

    @property
    def content_sha256(self) -> str:
        return str(self.payload["content_sha256"])


def canonical_file_hash(path: Path) -> str:
    content = path.resolve(strict=True).read_bytes()
    if b"\x00" not in content:
        content = content.replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(content).hexdigest()


def freeze_payload_hash(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("content_sha256", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_policy_freeze(path: Path, repository_root: Path) -> PolicyFreeze:
    path = path.resolve(strict=True)
    root = repository_root.resolve(strict=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("freeze_version") != FREEZE_VERSION:
        raise ValueError("unsupported policy freeze version")
    if payload.get("status") != "frozen":
        raise ValueError("policy manifest is not frozen")
    if payload.get("content_sha256") != freeze_payload_hash(payload):
        raise ValueError("policy freeze content hash mismatch")
    for artifact in payload.get("artifacts", []):
        candidate = (root / artifact["path"]).resolve(strict=True)
        if candidate != root and not candidate.is_relative_to(root):
            raise ValueError("policy artifact escapes repository")
        if canonical_file_hash(candidate) != artifact["sha256"]:
            raise ValueError(f"policy artifact hash mismatch: {artifact['path']}")
    return PolicyFreeze(path=path, payload=payload)
