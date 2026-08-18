from __future__ import annotations

from collections.abc import Sequence


def build_exec_command(
    *,
    prefix: Sequence[str],
    prompt: str,
    workspace: str,
    model: str,
    reasoning_effort: str,
    persist_session: bool,
) -> list[str]:
    persistence = [] if persist_session else ["--ephemeral"]
    return [
        *prefix,
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        *persistence,
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--cd",
        workspace,
        prompt,
    ]


def build_resume_command(
    *,
    prefix: Sequence[str],
    session_id: str,
    prompt: str,
    workspace: str,
    model: str,
    reasoning_effort: str,
) -> list[str]:
    if not session_id:
        raise ValueError("session_id must be non-empty")
    return [
        *prefix,
        "--ask-for-approval",
        "never",
        "--sandbox",
        "workspace-write",
        "--cd",
        workspace,
        "exec",
        "resume",
        "--json",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        session_id,
        prompt,
    ]
