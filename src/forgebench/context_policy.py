from __future__ import annotations

from dataclasses import dataclass, replace

from .types import ToolResult


@dataclass(frozen=True)
class ContextSnapshot:
    observations: tuple[ToolResult, ...]
    original_count: int
    original_chars: int
    retained_chars: int

    @property
    def dropped_count(self) -> int:
        return self.original_count - len(self.observations)

    @property
    def compacted(self) -> bool:
        return self.dropped_count > 0 or self.retained_chars < self.original_chars


class BoundedContextPolicy:
    """Keep recent evidence under a budget, prioritizing failed tool results."""

    def __init__(
        self,
        *,
        max_observations: int = 8,
        max_chars: int = 12_000,
        max_item_chars: int = 4_000,
    ) -> None:
        if min(max_observations, max_chars, max_item_chars) < 1:
            raise ValueError("context limits must be positive")
        self.max_observations = max_observations
        self.max_chars = max_chars
        self.max_item_chars = max_item_chars

    def select(self, observations: list[ToolResult]) -> ContextSnapshot:
        original_chars = sum(len(item.output) for item in observations)
        failures = [index for index, item in enumerate(observations) if not item.ok]
        successes = [index for index, item in enumerate(observations) if item.ok]
        priority = list(reversed(failures)) + list(reversed(successes))
        selected: dict[int, ToolResult] = {}
        remaining = self.max_chars

        for index in priority:
            if len(selected) >= self.max_observations or remaining <= 0:
                break
            item = observations[index]
            limit = min(self.max_item_chars, remaining)
            output = item.output
            if len(output) > limit:
                marker = "\n...[context truncated]"
                prefix_size = max(0, limit - len(marker))
                output = (output[:prefix_size] + marker)[:limit]
            retained = replace(
                item,
                output=output,
                metadata={
                    **item.metadata,
                    **({"context_truncated": True} if output != item.output else {}),
                },
            )
            selected[index] = retained
            remaining -= len(output)

        ordered = tuple(selected[index] for index in sorted(selected))
        return ContextSnapshot(
            ordered,
            len(observations),
            original_chars,
            sum(len(item.output) for item in ordered),
        )


class UnboundedContextPolicy:
    def select(self, observations: list[ToolResult]) -> ContextSnapshot:
        size = sum(len(item.output) for item in observations)
        return ContextSnapshot(tuple(observations), len(observations), size, size)
