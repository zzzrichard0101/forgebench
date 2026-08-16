from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from .types import ToolCall, ToolResult
from .workspace import WorkspaceError, resolve_workspace_path


class ToolGateway:
    """Typed, repository-scoped tool boundary.

    It does not invoke a shell. Commands are argument arrays and executable names
    must be explicitly allowed by the runner configuration.
    """

    def __init__(
        self,
        workspace: Path,
        *,
        command_allowlist: set[str] | None = None,
        max_output_chars: int = 20_000,
    ) -> None:
        self.workspace = workspace.resolve(strict=True)
        self.command_allowlist = command_allowlist or set()
        self.max_output_chars = max_output_chars
        self._handlers: dict[str, Callable[[dict[str, Any]], ToolResult]] = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "list_files": self._list_files,
            "search_text": self._search_text,
            "run_command": self._run_command,
        }

    @property
    def schemas(self) -> tuple[dict[str, Any], ...]:
        return (
            _schema("read_file", {"path": "string"}, ["path"]),
            _schema("write_file", {"path": "string", "content": "string"}, ["path", "content"]),
            _schema("list_files", {"path": "string"}, []),
            _schema("search_text", {"query": "string", "path": "string"}, ["query"]),
            {
                "name": "run_command",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "argv": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        "cwd": {"type": "string"},
                        "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 120},
                    },
                    "required": ["argv"],
                    "additionalProperties": False,
                },
            },
        )

    def execute(self, call: ToolCall) -> ToolResult:
        handler = self._handlers.get(call.name)
        if handler is None:
            return ToolResult(call.name, False, f"unknown tool: {call.name}")
        try:
            return handler(call.arguments)
        except (KeyError, TypeError, ValueError, OSError, WorkspaceError) as exc:
            return ToolResult(call.name, False, f"{type(exc).__name__}: {exc}")

    def _read_file(self, args: dict[str, Any]) -> ToolResult:
        path = resolve_workspace_path(self.workspace, _string(args, "path"), must_exist=True)
        if not path.is_file():
            raise ValueError("path is not a file")
        content = path.read_text(encoding="utf-8")
        return ToolResult("read_file", True, self._bounded(content), {"path": str(path.relative_to(self.workspace))})

    def _write_file(self, args: dict[str, Any]) -> ToolResult:
        relative = _string(args, "path")
        content = _string(args, "content")
        path = resolve_workspace_path(self.workspace, relative, must_exist=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return ToolResult("write_file", True, f"wrote {len(content)} chars", {"path": relative})

    def _list_files(self, args: dict[str, Any]) -> ToolResult:
        relative = args.get("path", ".")
        if not isinstance(relative, str):
            raise TypeError("path must be a string")
        path = resolve_workspace_path(self.workspace, relative, must_exist=True)
        if not path.is_dir():
            raise ValueError("path is not a directory")
        files = sorted(str(item.relative_to(self.workspace)).replace("\\", "/") for item in path.rglob("*") if item.is_file())
        return ToolResult("list_files", True, self._bounded("\n".join(files)), {"count": len(files)})

    def _search_text(self, args: dict[str, Any]) -> ToolResult:
        query = _string(args, "query")
        relative = args.get("path", ".")
        if not isinstance(relative, str):
            raise TypeError("path must be a string")
        root = resolve_workspace_path(self.workspace, relative, must_exist=True)
        candidates = [root] if root.is_file() else sorted(item for item in root.rglob("*") if item.is_file())
        matches: list[str] = []
        for path in candidates:
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if query in line:
                    rel = str(path.relative_to(self.workspace)).replace("\\", "/")
                    matches.append(f"{rel}:{line_number}:{line}")
        return ToolResult("search_text", True, self._bounded("\n".join(matches)), {"count": len(matches)})

    def _run_command(self, args: dict[str, Any]) -> ToolResult:
        argv = args.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise TypeError("argv must be a non-empty string array")
        executable = Path(argv[0]).name.lower()
        if executable not in {item.lower() for item in self.command_allowlist}:
            raise ValueError(f"executable is not allowed: {executable}")
        cwd_value = args.get("cwd", ".")
        if not isinstance(cwd_value, str):
            raise TypeError("cwd must be a string")
        cwd = resolve_workspace_path(self.workspace, cwd_value, must_exist=True)
        timeout = args.get("timeout_seconds", 30)
        if not isinstance(timeout, int) or not 1 <= timeout <= 120:
            raise ValueError("timeout_seconds must be between 1 and 120")
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        output = completed.stdout + completed.stderr
        return ToolResult(
            "run_command",
            completed.returncode == 0,
            self._bounded(output),
            {"exit_code": completed.returncode},
        )

    def _bounded(self, value: str) -> str:
        if len(value) <= self.max_output_chars:
            return value
        return value[: self.max_output_chars] + "\n...[truncated]"


def _string(args: dict[str, Any], key: str) -> str:
    value = args[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _schema(name: str, properties: dict[str, str], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "input_schema": {
            "type": "object",
            "properties": {key: {"type": value} for key, value in properties.items()},
            "required": required,
            "additionalProperties": False,
        },
    }

