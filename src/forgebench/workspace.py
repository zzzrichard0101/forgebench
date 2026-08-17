from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class WorkspaceError(ValueError):
    pass


def create_isolated_workspace(
    seed: Path,
    runs_root: Path,
    run_id: str,
    *,
    preserve_symlinks: bool = False,
) -> Path:
    """Copy a seed directory into a new, validated run-owned workspace."""

    seed = seed.resolve(strict=True)
    runs_root = runs_root.resolve()
    runs_root.mkdir(parents=True, exist_ok=True)
    target = (runs_root / run_id / "workspace").resolve()
    if not target.is_relative_to(runs_root):
        raise WorkspaceError("run workspace escapes runs root")
    if target.exists():
        raise WorkspaceError(f"run workspace already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=False)
    shutil.copytree(seed, target, symlinks=preserve_symlinks)
    return target


def initialize_git_workspace(workspace: Path) -> None:
    """Create a local Git baseline so agent inspection cannot escape to a parent repo."""

    commands = (
        ["git", "init", "--quiet"],
        ["git", "add", "--all"],
        [
            "git",
            "-c",
            "user.name=ForgeBench",
            "-c",
            "user.email=forgebench@localhost",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "ForgeBench seed",
        ],
    )
    for command in commands:
        try:
            subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise WorkspaceError("failed to initialize isolated Git workspace") from exc


def resolve_workspace_path(root: Path, relative_path: str, *, must_exist: bool) -> Path:
    """Resolve a user-controlled path while enforcing the workspace boundary."""

    root = root.resolve(strict=True)
    # Resolve the boundary before enforcing existence. Otherwise a missing path
    # outside the workspace is misclassified as a filesystem error instead of a
    # policy violation.
    candidate = (root / relative_path).resolve(strict=False)
    if candidate != root and not candidate.is_relative_to(root):
        raise WorkspaceError(f"path escapes workspace: {relative_path}")
    if must_exist:
        candidate = candidate.resolve(strict=True)
    return candidate
