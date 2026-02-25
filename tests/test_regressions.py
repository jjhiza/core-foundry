"""Regression tests for specific bugs found during code review."""

import pytest
from corefoundry.core import ToolRegistry


class TestKeyErrorMessage:
    """Regression: core.py:221 used f\"Tool '{tool}'\" instead of f\"Tool '{name}'\"

    This caused the error message to print "Tool 'None' not found" instead of
    showing the actual tool name that was looked up.
    """

    def test_keyerror_includes_tool_name(self):
        """The KeyError message must include the name that was looked up."""
        reg = ToolRegistry()
        with pytest.raises(KeyError, match="missing_tool"):
            reg.get_callable("missing_tool")

    def test_keyerror_includes_different_name(self):
        """Verify it's not a hardcoded string — try multiple names."""
        reg = ToolRegistry()

        with pytest.raises(KeyError, match="foo_bar_baz"):
            reg.get_callable("foo_bar_baz")

        with pytest.raises(KeyError, match="another_name"):
            reg.get_callable("another_name")

    def test_keyerror_message_does_not_contain_none(self):
        """The old bug printed 'None' — make sure that never happens."""
        reg = ToolRegistry()
        with pytest.raises(KeyError) as exc_info:
            reg.get_callable("xyz")
        assert "None" not in str(exc_info.value)
        assert "xyz" in str(exc_info.value)


class TestModelDumpNotDict:
    """Regression: get_json() used deprecated .dict() which could break in future Pydantic."""

    def test_get_json_serialization_works(self):
        """Verify get_json still works after the .dict() -> .model_dump() fix."""
        reg = ToolRegistry()

        @reg.register(
            name="test_dump",
            description="test",
            input_schema={
                "properties": {
                    "x": {"type": "string", "description": "a value"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["x"],
            },
        )
        def test_dump(x, tags=None):
            pass

        result = reg.get_json()
        assert len(result) == 1
        schema = result[0]["input_schema"]
        assert schema["type"] == "object"
        assert "x" in schema["properties"]
        assert schema["properties"]["x"]["type"] == "string"
        assert schema["properties"]["x"]["description"] == "a value"
        assert schema["properties"]["tags"]["items"] == {"type": "string"}
        assert schema["required"] == ["x"]

    def test_get_json_excludes_none_values(self):
        """None values should not appear in serialized output."""
        reg = ToolRegistry()

        @reg.register(
            name="minimal_dump",
            description="test",
            input_schema={
                "properties": {"x": {"type": "string"}},
            },
        )
        def minimal_dump(x):
            pass

        result = reg.get_json()
        prop = result[0]["input_schema"]["properties"]["x"]
        # description is None; should be excluded from serialized output
        assert "description" not in prop
        assert "enum" not in prop
        assert "items" not in prop
