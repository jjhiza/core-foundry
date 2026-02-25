from __future__ import annotations

import pkgutil
import importlib

from typing import Any, List, Dict, Callable, Optional
from pydantic import BaseModel, Field, ValidationError, model_validator


class ToolProperty(BaseModel):
    """A single property in a tool's input schema

    Attributes:
        type: The JSON Schema type (e.g., "string", "integer", "boolean", "array", "object")
        description: Optional description of what this property represents
        items: Schema definition for array items (required when type is "array")
        enum: List of allowed values for enum types
        properties: Schema definitions for object properties (when type is "object")
        required: List of required property names (when type is "object")

    Examples:
        >>> prop = ToolProperty(type="string", description="A name")
        >>> prop.type
        'string'

        >>> prop = ToolProperty(type="array", items={"type": "string"})
        >>> prop.items
        {'type': 'string'}

        >>> prop = ToolProperty(type="string", enum=["a", "b"])
        >>> prop.enum
        ['a', 'b']
    """

    type: str
    description: Optional[str] = None
    items: Optional[Dict[str, Any]] = None
    enum: Optional[List[Any]] = None
    properties: Optional[Dict[str, Any]] = None
    required: Optional[List[str]] = None

    @model_validator(mode='after')
    def validate_schema_requirements(self):
        """Validate OpenAPI 3.0 schema requirements"""
        if self.type == "array" and self.items is None:
            raise ValueError("items field is required when type is 'array'")
        return self


class InputSchema(BaseModel):
    """JSON Schema definition for tool inputs

    Attributes:
        type: Schema type, typically "object" for tool parameters

        properties: Dictionary mapping parameter names
        to their ToolProperty definitions

        required: List of required parameter names

    Examples:
        >>> schema = InputSchema()
        >>> schema.type
        'object'
        >>> schema.properties
        {}

        >>> schema = InputSchema(**{
        ...     "properties": {"name": {"type": "string"}},
        ...     "required": ["name"],
        ... })
        >>> "name" in schema.properties
        True
        >>> schema.required
        ['name']
    """

    type: str = "object"
    properties: Dict[str, ToolProperty] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def convert_property_dicts(cls, data):
        """Convert raw property dictionaries to ToolProperty instances"""
        if isinstance(data, dict) and 'properties' in data:
            properties = data['properties']
            if isinstance(properties, dict):
                converted_properties = {}
                for prop_name, prop_def in properties.items():
                    if isinstance(prop_def, dict):
                        converted_properties[prop_name] = ToolProperty(**prop_def)
                    else:
                        converted_properties[prop_name] = prop_def
                data['properties'] = converted_properties
        return data


class ToolDefinition(BaseModel):
    """Complete definition of a tool, including metadata and callable

    Attributes:
        name: Unique identifier for the tool

        description: Human-readable description of what the tool does

        input_schema: JSON Schema defining the tool's input parameters

        callable: The actual Python function to execute
        (excluded from serialization)
    """

    name: str
    description: str
    input_schema: InputSchema
    # callable is excluded from serialization and used for runtime invocation
    callable: Optional[Callable[..., Any]] = Field(default=None, exclude=True)


class ToolRegistry:
    """Registry for managing tool definitions and their callables

    The registry provides:
    - Decorator-based tool registration
    - Auto-discovery from Python packages
    - JSON serialization for LLM providers
    - Runtime tool execution
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry.

        Examples:
            >>> reg = ToolRegistry()
            >>> reg.list_names()
            []
        """
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        """Decorator to register a callable as a tool

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
        """Auto-discover and register tools from a Python package

        Imports all modules in the specified package

        Modules should use the
        @registry.register decorator to register tools at import time

        Args:
            package_name: Fully qualified package name (e.g., "my_app.tools")

        Raises:
            ImportError: If the package cannot be imported

        Example:
            >>> registry.autodiscover("examples.my_tools")
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
        """Get all registered tool definitions

        Returns:
            List of all ToolDefinition objects in the registry

        Examples:
            >>> reg = ToolRegistry()
            >>> reg.get_all()
            []
        """
        return list(self._tools.values())

    def get_json(self) -> List[Dict[str, Any]]:
        """Export tools as JSON-compatible dictionaries

        Returns tool definitions in a format compatible with Anthropic's API

        For OpenAI compatibility, adapters should transform this output

        Returns:
            List of dictionaries with keys: name, description, input_schema
        """
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema.model_dump(exclude_none=True),
            }
            for t in self._tools.values()
        ]

    def get_callable(self, name: str) -> Callable[..., Any]:
        """Retrieve the callable function for a registered tool

        Args:
            name: Name of the tool to retrieve

        Returns:
            The callable function associated with the tool

        Raises:
            KeyError: If no tool with the given name exists

            RuntimeError: If the tool has no callable attached
        """
        tool = self._tools.get(name)

        if not tool:
            raise KeyError(f"Tool '{name}' not found")
        if tool.callable is None:
            raise RuntimeError(f"Tool '{name}' has no callable attached")
        return tool.callable

    def list_names(self) -> List[str]:
        """Get the names of all registered tools

        Returns:
            List of tool names as strings

        Examples:
            >>> reg = ToolRegistry()
            >>> reg.list_names()
            []
        """
        return list(self._tools.keys())


# Global registry instance
registry = ToolRegistry()
