from __future__ import annotations

import pkgutil
import importlib

from typing import Any, List, Dict, Callable, Optional
from pydantic import BaseModel, Field, ValidationError


class ToolProperty(BaseModel):
    type: str
    description: Optional[str] = None


class InputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, ToolProperty] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: InputSchema
    # callable is excluded from serialization and used for runtime invocation
    callable: Optional[Callable[..., Any]] = Field(default=None, exclude=True)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Decorator to register a callable as a tool.
        Example:
            @registry.register(
                description="Read a file.",
                input_schema={
                    "properties": {"file_path": {"type": "string"}},
                    "required": ["file_path"]
                }
            )
            def read_file(file_path: str): ...
        """

        def decorator(func: Callable[..., Any]):
            tool_name = name or func.__name__

            try:
                schema = InputSchema(**(input_schema or {}))
            except ValidationError as ve:
                raise ValueError(f"Invalid input_schema for tool '{tool_name}': {ve}")

            tool = ToolDefinition(
                name=tool_name,
                description=description or func.__doc__ or "No description provided",
                input_schema=schema,
                callable=func,
            )

            if tool_name in self._tools:
                raise ValueError(f"Tool '{tool_name}' already registered")

            self._tools[tool_name] = tool
            return func

        return decorator

    def autodiscover(self, package_name: str) -> None:
        """
        Import all modules in the package. Modules should import registry and
        register tools at import-time (via decorator).
        E.g. registry.autodiscover("examples.my_tools")
        """

        try:
            package = importlib.import_module(package_name)
        except ImportError as ie:
            raise ImportError(f"Could not import package '{package_name}': {ie}")

        if not hasattr(package, "__path__"):
            # package is a module, not a package
            return

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            importlib.import_module(f"{package_name}.{module_name}")

    def get_all(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_json(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema.dict(exclude_none=True),
            }
            for t in self._tools.values()
        ]

    def get_callable(self, name: str) -> Callable[..., Any]:
        tool = self._tools.get(name)

        if not tool:
            raise KeyError(f"Tool '{tool}' not found")
        if tool.callable is None:
            raise RuntimeError(f"Tool '{name}' has no callable attached")
        return tool.callable

    def list_names(self) -> List[str]:
        return list(self._tools.keys())


# Global registry instance
registry = ToolRegistry()
