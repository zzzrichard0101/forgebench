from __future__ import annotations

from collections import deque
from typing import Protocol, Sequence

from .types import ModelAction, ModelContext


class ModelAdapter(Protocol):
    """Provider-neutral model boundary used by the harness."""

    @property
    def model_id(self) -> str: ...

    def next_action(self, context: ModelContext) -> ModelAction: ...


class ScriptedModelAdapter:
    """Deterministic adapter for infrastructure tests, never benchmark scores."""

    def __init__(self, actions: Sequence[ModelAction], model_id: str = "scripted-v1") -> None:
        self._actions = deque(actions)
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    def next_action(self, context: ModelContext) -> ModelAction:
        if not self._actions:
            return ModelAction.finish("Script exhausted without an explicit final action.")
        return self._actions.popleft()

