from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IGNORED_SEED_PARTS = {".git", "__pycache__", ".pytest_cache"}


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class TaskBundle:
    task: dict[str, Any]
    task_path: Path
    seed_path: Path


class BenchmarkCatalog:
    def __init__(self, repository_root: Path, manifest_path: Path) -> None:
        self.repository_root = repository_root.resolve(strict=True)
        self.manifest_path = manifest_path.resolve(strict=True)
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        records = payload.get("tasks")
        if not isinstance(records, list) or not records:
            raise CatalogError("benchmark manifest must contain tasks")
        self.snapshot = payload.get("snapshot", "unknown")
        self.frozen = bool(payload.get("frozen", False))
        self._bundles: dict[str, TaskBundle] = {}
        for record in records:
            bundle = self._load_bundle(record)
            task_id = bundle.task["id"]
            if task_id in self._bundles:
                raise CatalogError(f"duplicate task id: {task_id}")
            self._bundles[task_id] = bundle

    def list(self) -> tuple[TaskBundle, ...]:
        return tuple(self._bundles.values())

    def get(self, task_id: str) -> TaskBundle:
        try:
            return self._bundles[task_id]
        except KeyError as exc:
            available = ", ".join(self._bundles)
            raise CatalogError(
                f"unknown task id {task_id!r}; available: {available}"
            ) from exc

    def _load_bundle(self, record: dict[str, Any]) -> TaskBundle:
        relative_task_path = record.get("task_path")
        if not isinstance(relative_task_path, str):
            raise CatalogError("manifest task_path must be a string")
        task_path = _resolve_inside(self.repository_root, relative_task_path)
        task = json.loads(task_path.read_text(encoding="utf-8"))
        for field in ("id", "version", "family", "difficulty", "split"):
            if record.get(field) != task.get(field):
                raise CatalogError(
                    f"manifest mismatch for {relative_task_path}: {field}"
                )
        seed_source = task.get("seed_repo", {}).get("source")
        if not isinstance(seed_source, str):
            raise CatalogError(f"task {task.get('id')} has no seed source")
        seed_path = _resolve_inside(self.repository_root, seed_source)
        if not seed_path.is_dir():
            raise CatalogError(f"seed directory does not exist: {seed_source}")
        return TaskBundle(task, task_path, seed_path)


def hash_seed(root: Path) -> str:
    root = root.resolve(strict=True)
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not (set(path.relative_to(root).parts) & IGNORED_SEED_PARTS)
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def _resolve_inside(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve(strict=True)
    if candidate != root and not candidate.is_relative_to(root):
        raise CatalogError(f"manifest path escapes repository: {relative_path}")
    return candidate
