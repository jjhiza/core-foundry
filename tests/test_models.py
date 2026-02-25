"""Unit tests for Pydantic models: ToolProperty, InputSchema, ToolDefinition."""

import pytest
from pydantic import ValidationError

from corefoundry.core import ToolProperty, InputSchema, ToolDefinition


# ---------------------------------------------------------------------------
# ToolProperty
# ---------------------------------------------------------------------------

class TestToolProperty:
    """Tests for the ToolProperty model."""

    def test_string_property(self):
        prop = ToolProperty(type="string", description="a name")
        assert prop.type == "string"
        assert prop.description == "a name"

    def test_integer_property(self):
        prop = ToolProperty(type="integer")
        assert prop.type == "integer"
        assert prop.description is None

    def test_boolean_property(self):
        prop = ToolProperty(type="boolean", description="flag")
        assert prop.type == "boolean"

    def test_enum_property(self):
        prop = ToolProperty(type="string", enum=["a", "b", "c"])
        assert prop.enum == ["a", "b", "c"]

    def test_array_property_with_items(self):
        prop = ToolProperty(type="array", items={"type": "string"})
        assert prop.type == "array"
        assert prop.items == {"type": "string"}

    def test_array_property_without_items_raises(self):
        with pytest.raises(ValidationError, match="items field is required"):
            ToolProperty(type="array")

    def test_object_property_with_nested_properties(self):
        prop = ToolProperty(
            type="object",
            properties={"name": {"type": "string"}},
            required=["name"],
        )
        assert prop.properties == {"name": {"type": "string"}}
        assert prop.required == ["name"]

    def test_optional_fields_default_none(self):
        prop = ToolProperty(type="string")
        assert prop.description is None
        assert prop.items is None
        assert prop.enum is None
        assert prop.properties is None
        assert prop.required is None

    def test_number_property(self):
        prop = ToolProperty(type="number", description="a float")
        assert prop.type == "number"


# ---------------------------------------------------------------------------
# InputSchema
# ---------------------------------------------------------------------------

class TestInputSchema:
    """Tests for the InputSchema model."""

    def test_default_schema(self):
        schema = InputSchema()
        assert schema.type == "object"
        assert schema.properties == {}
        assert schema.required == []

    def test_schema_with_properties(self):
        schema = InputSchema(
            properties={
                "name": ToolProperty(type="string", description="person name"),
                "age": ToolProperty(type="integer"),
            },
            required=["name"],
        )
        assert "name" in schema.properties
        assert "age" in schema.properties
        assert schema.required == ["name"]

    def test_schema_from_raw_dict(self):
        """Test that raw dicts in properties are converted to ToolProperty."""
        schema = InputSchema(
            **{
                "properties": {
                    "text": {"type": "string", "description": "input text"},
                },
                "required": ["text"],
            }
        )
        assert isinstance(schema.properties["text"], ToolProperty)
        assert schema.properties["text"].type == "string"

    def test_schema_validates_array_items_in_property(self):
        with pytest.raises(ValidationError, match="items field is required"):
            InputSchema(
                **{
                    "properties": {
                        "tags": {"type": "array"},  # missing items
                    },
                }
            )

    def test_schema_model_dump_excludes_none(self):
        schema = InputSchema(
            **{
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            }
        )
        dumped = schema.model_dump(exclude_none=True)
        assert dumped["type"] == "object"
        assert "text" in dumped["properties"]
        # description was None, should be excluded
        assert "description" not in dumped["properties"]["text"]


# ---------------------------------------------------------------------------
# ToolDefinition
# ---------------------------------------------------------------------------

class TestToolDefinition:
    """Tests for the ToolDefinition model."""

    def test_basic_tool_definition(self):
        schema = InputSchema()
        tool = ToolDefinition(
            name="my_tool",
            description="Does something",
            input_schema=schema,
        )
        assert tool.name == "my_tool"
        assert tool.description == "Does something"
        assert tool.callable is None

    def test_tool_definition_with_callable(self):
        def my_fn():
            return 42

        schema = InputSchema()
        tool = ToolDefinition(
            name="fn_tool",
            description="returns 42",
            input_schema=schema,
            callable=my_fn,
        )
        assert tool.callable is my_fn
        assert tool.callable() == 42

    def test_callable_excluded_from_serialization(self):
        def my_fn():
            return 1

        schema = InputSchema()
        tool = ToolDefinition(
            name="fn_tool",
            description="a tool",
            input_schema=schema,
            callable=my_fn,
        )
        dumped = tool.model_dump()
        assert "callable" not in dumped

    def test_tool_definition_requires_name_and_description(self):
        schema = InputSchema()
        with pytest.raises(ValidationError):
            ToolDefinition(description="no name", input_schema=schema)

        with pytest.raises(ValidationError):
            ToolDefinition(name="no_desc", input_schema=schema)
