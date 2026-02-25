"""Integration tests — end-to-end flows through multiple components."""

import json
from unittest.mock import MagicMock

from corefoundry.core import ToolRegistry
from corefoundry.agent import Agent
from agent_adapters.openai_adapter import OpenAIAdapter
from agent_adapters.anthropic_adapter import AnthropicAdapter


class TestEndToEndToolLifecycle:
    """Test the full lifecycle: register -> serialize -> call."""

    def test_register_serialize_and_call(self):
        reg = ToolRegistry()

        @reg.register(
            name="multiply",
            description="Multiply two numbers",
            input_schema={
                "properties": {
                    "a": {"type": "number", "description": "first number"},
                    "b": {"type": "number", "description": "second number"},
                },
                "required": ["a", "b"],
            },
        )
        def multiply(a, b):
            return a * b

        # Serialize for LLM consumption
        tools_json = reg.get_json()
        assert len(tools_json) == 1
        assert tools_json[0]["name"] == "multiply"

        # Simulate an LLM returning a tool call — look up and invoke
        fn = reg.get_callable("multiply")
        result = fn(a=6, b=7)
        assert result == 42

    def test_agent_wraps_registry_end_to_end(self):
        reg = ToolRegistry()

        @reg.register(
            name="reverse",
            description="Reverse a string",
            input_schema={
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )
        def reverse(text: str):
            return text[::-1]

        agent = Agent(name="ReverseAgent", description="reverses things")
        agent._registry = reg

        # Check JSON output is parseable and correct
        parsed = json.loads(agent.available_tools_json())
        assert len(parsed) == 1
        assert parsed[0]["name"] == "reverse"

        # Call through agent
        assert agent.call_tool("reverse", text="hello") == "olleh"

    def test_multiple_tools_complex_schemas(self):
        reg = ToolRegistry()

        @reg.register(
            name="search",
            description="Search items",
            input_schema={
                "properties": {
                    "query": {"type": "string", "description": "search query"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "filter tags",
                    },
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
        )
        def search(query, tags=None, limit=10):
            return {"query": query, "tags": tags or [], "limit": limit}

        @reg.register(
            name="format",
            description="Format output",
            input_schema={
                "properties": {
                    "data": {"type": "object", "properties": {"key": {"type": "string"}}},
                    "style": {"type": "string", "enum": ["json", "text"]},
                },
                "required": ["data", "style"],
            },
        )
        def format_output(data, style):
            if style == "json":
                return json.dumps(data)
            return str(data)

        tools_json = reg.get_json()
        assert len(tools_json) == 2
        names = {t["name"] for t in tools_json}
        assert names == {"search", "format"}

        # Invoke search
        result = reg.get_callable("search")(query="hello", tags=["a"], limit=5)
        assert result == {"query": "hello", "tags": ["a"], "limit": 5}

        # Invoke format
        result = reg.get_callable("format")(data={"key": "val"}, style="json")
        assert result == '{"key": "val"}'


class TestAdapterIntegration:
    """Test adapters integrated with the registry end-to-end."""

    def test_openai_adapter_receives_correct_tool_schema(self):
        reg = ToolRegistry()

        @reg.register(
            name="ping",
            description="Return pong",
            input_schema={"properties": {"msg": {"type": "string"}}},
        )
        def ping(msg: str):
            return "pong"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = "response"

        adapter = OpenAIAdapter(client=mock_client, registry=reg)
        adapter.call_with_tools("ping something")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        tools = call_kwargs["tools"]
        assert tools[0]["name"] == "ping"
        assert tools[0]["input_schema"]["properties"]["msg"]["type"] == "string"

    def test_anthropic_adapter_receives_correct_tool_schema(self):
        reg = ToolRegistry()

        @reg.register(
            name="pong",
            description="Return ping",
            input_schema={
                "properties": {"msg": {"type": "string"}},
                "required": ["msg"],
            },
        )
        def pong(msg: str):
            return "ping"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = "response"

        adapter = AnthropicAdapter(client=mock_client, registry=reg)
        adapter.call_with_tools("pong something")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        tools = call_kwargs["tools"]
        assert tools[0]["name"] == "pong"
        assert tools[0]["input_schema"]["properties"]["msg"]["type"] == "string"
        assert "msg" in tools[0]["input_schema"]["required"]
