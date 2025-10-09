from __future__ import annotations

import json

from typing import Any
from .core import registry


class Agent:
    """
    Lightweight, LLM-agnostic agent wrapper that can:
      - autodiscover tools from a package
      - expose JSON definitions for model adapters
      - call tools at runtime
    """

    def __init__(
        self, name: str, description: str = "", auto_tools_pkg: str | None = None
    ):
        self.name = name
        self.description = description

        if auto_tools_pkg:
            registry.autodiscover(auto_tools_pkg)
        self._registry = registry

    def available_tools_json(self) -> str:
        """Return available tools as JSON (suitable for LLM tool lists)."""
        return json.dumps(self._registry.get_json(), indent=2)

    def call_tool(self, name: str, **kwargs: Any) -> Any:
        """Call a registered tool by name."""
        func = self._registry.get_callable(name)
        return func(**kwargs)

    def tool_names(self):
        return self._registry.list_names()
