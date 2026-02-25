"""Unit tests for ToolRegistry — registration, lookup, serialization, error paths."""

import pytest

from corefoundry.core import ToolRegistry


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    """Tests for the @registry.register decorator."""

    def test_register_with_explicit_name(self, fresh_registry):
        @fresh_registry.register(
            name="greet",
            description="Say hello",
            input_schema={
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )
        def greet(name: str):
            return f"Hello, {name}"

        assert "greet" in fresh_registry.list_names()

    def test_register_defaults_to_function_name(self, fresh_registry):
        @fresh_registry.register(
            description="Echo",
            input_schema={"properties": {"msg": {"type": "string"}}},
        )
        def my_echo(msg: str):
            return msg

        assert "my_echo" in fresh_registry.list_names()

    def test_register_defaults_description_to_docstring(self, fresh_registry):
        @fresh_registry.register(
            input_schema={"properties": {"x": {"type": "integer"}}},
        )
        def documented(x: int):
            """A documented tool."""
            return x

        tools = fresh_registry.get_json()
        tool_json = next(t for t in tools if t["name"] == "documented")
        assert tool_json["description"] == "A documented tool."

    def test_register_defaults_description_to_fallback(self, fresh_registry):
        @fresh_registry.register(
            input_schema={"properties": {"x": {"type": "integer"}}},
        )
        def no_doc(x: int):
            return x

        tools = fresh_registry.get_json()
        tool_json = next(t for t in tools if t["name"] == "no_doc")
        assert tool_json["description"] == "No description provided"

    def test_register_with_no_schema(self, fresh_registry):
        @fresh_registry.register(description="bare tool")
        def bare():
            return "ok"

        assert "bare" in fresh_registry.list_names()

    def test_duplicate_registration_raises(self, fresh_registry):
        @fresh_registry.register(name="dup", description="first")
        def first():
            pass

        with pytest.raises(ValueError, match="already registered"):
            @fresh_registry.register(name="dup", description="second")
            def second():
                pass

    def test_invalid_schema_raises_valueerror(self, fresh_registry):
        with pytest.raises(ValueError, match="Invalid input_schema"):
            @fresh_registry.register(
                name="bad",
                description="bad schema",
                input_schema={
                    "properties": {
                        "tags": {"type": "array"},  # missing items
                    },
                },
            )
            def bad():
                pass

    def test_decorator_returns_original_function(self, fresh_registry):
        @fresh_registry.register(name="orig", description="test")
        def original():
            return "original"

        assert original() == "original"


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

class TestRetrieval:
    """Tests for get_callable, get_all, get_json, list_names."""

    def test_get_callable_returns_function(self, fresh_registry):
        @fresh_registry.register(
            name="add",
            description="add two numbers",
            input_schema={
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        )
        def add(a: int, b: int):
            return a + b

        fn = fresh_registry.get_callable("add")
        assert fn(2, 3) == 5

    def test_get_callable_missing_tool_raises_keyerror(self, fresh_registry):
        with pytest.raises(KeyError, match="Tool 'nonexistent' not found"):
            fresh_registry.get_callable("nonexistent")

    def test_get_callable_no_callable_raises_runtime_error(self, fresh_registry):
        """Manually insert a tool with callable=None to test the RuntimeError path."""
        from corefoundry.core import ToolDefinition, InputSchema

        tool = ToolDefinition(
            name="ghost",
            description="no callable",
            input_schema=InputSchema(),
            callable=None,
        )
        fresh_registry._tools["ghost"] = tool

        with pytest.raises(RuntimeError, match="no callable attached"):
            fresh_registry.get_callable("ghost")

    def test_get_all_returns_list_of_tool_definitions(self, fresh_registry):
        @fresh_registry.register(name="t1", description="tool 1")
        def t1():
            pass

        @fresh_registry.register(name="t2", description="tool 2")
        def t2():
            pass

        from corefoundry.core import ToolDefinition

        all_tools = fresh_registry.get_all()
        assert len(all_tools) == 2
        assert all(isinstance(t, ToolDefinition) for t in all_tools)

    def test_get_json_structure(self, fresh_registry):
        @fresh_registry.register(
            name="json_tool",
            description="returns json",
            input_schema={
                "properties": {"x": {"type": "string", "description": "val"}},
                "required": ["x"],
            },
        )
        def json_tool(x: str):
            return x

        result = fresh_registry.get_json()
        assert len(result) == 1
        entry = result[0]
        assert entry["name"] == "json_tool"
        assert entry["description"] == "returns json"
        assert "input_schema" in entry
        assert entry["input_schema"]["type"] == "object"
        assert "x" in entry["input_schema"]["properties"]

    def test_get_json_excludes_none_fields(self, fresh_registry):
        @fresh_registry.register(
            name="minimal",
            description="minimal",
            input_schema={"properties": {"x": {"type": "string"}}},
        )
        def minimal(x: str):
            return x

        result = fresh_registry.get_json()
        prop = result[0]["input_schema"]["properties"]["x"]
        # description is None and should be excluded
        assert "description" not in prop

    def test_list_names_returns_strings(self, fresh_registry):
        @fresh_registry.register(name="alpha", description="a")
        def alpha():
            pass

        @fresh_registry.register(name="beta", description="b")
        def beta():
            pass

        names = fresh_registry.list_names()
        assert set(names) == {"alpha", "beta"}

    def test_empty_registry(self, fresh_registry):
        assert fresh_registry.get_all() == []
        assert fresh_registry.get_json() == []
        assert fresh_registry.list_names() == []


# ---------------------------------------------------------------------------
# Autodiscover
# ---------------------------------------------------------------------------

class TestAutodiscover:
    """Tests for the autodiscover method."""

    def test_autodiscover_bad_package_raises_importerror(self, fresh_registry):
        with pytest.raises(ImportError, match="Could not import package"):
            fresh_registry.autodiscover("nonexistent.package.xyz")

    def test_autodiscover_module_not_package(self, fresh_registry):
        """autodiscover on a plain module (no __path__) should return silently."""
        # importlib.import_module("json") gives a module without __path__
        fresh_registry.autodiscover("json")
        # should not raise — it just returns early
