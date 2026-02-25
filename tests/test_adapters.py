"""Unit tests for adapters (OpenAI, Anthropic) using mocked clients."""

from unittest.mock import MagicMock, patch
import pytest

from corefoundry.core import ToolRegistry
from agent_adapters.base import BaseAdapter
from agent_adapters.openai_adapter import OpenAIAdapter
from agent_adapters.anthropic_adapter import AnthropicAdapter


@pytest.fixture()
def registry_with_tool():
    """A fresh registry with one tool registered."""
    reg = ToolRegistry()

    @reg.register(
        name="echo",
        description="Echo input",
        input_schema={
            "properties": {"msg": {"type": "string"}},
            "required": ["msg"],
        },
    )
    def echo(msg: str):
        return f"echo:{msg}"

    return reg


# ---------------------------------------------------------------------------
# BaseAdapter
# ---------------------------------------------------------------------------

class TestBaseAdapter:
    """Tests for the abstract BaseAdapter."""

    def test_cannot_instantiate_directly(self, registry_with_tool):
        with pytest.raises(TypeError):
            BaseAdapter(registry_with_tool)

    def test_concrete_subclass_must_implement_methods(self, registry_with_tool):
        class IncompleteAdapter(BaseAdapter):
            pass

        with pytest.raises(TypeError):
            IncompleteAdapter(registry_with_tool)

    def test_concrete_subclass_works(self, registry_with_tool):
        class ConcreteAdapter(BaseAdapter):
            def generate(self, prompt: str):
                return "generated"

            def call_with_tools(self, prompt: str):
                return "with tools"

        adapter = ConcreteAdapter(registry_with_tool)
        assert adapter.generate("hi") == "generated"
        assert adapter.call_with_tools("hi") == "with tools"
        assert adapter.registry is registry_with_tool


# ---------------------------------------------------------------------------
# OpenAIAdapter
# ---------------------------------------------------------------------------

class TestOpenAIAdapter:
    """Tests for the OpenAI adapter with mocked client."""

    def test_generate_calls_client(self, registry_with_tool):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = "mock_response"

        adapter = OpenAIAdapter(
            client=mock_client,
            registry=registry_with_tool,
            model="gpt-4o-mini",
        )
        result = adapter.generate("Hello")

        assert result == "mock_response"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )

    def test_call_with_tools_passes_tools(self, registry_with_tool):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = "mock_tool_response"

        adapter = OpenAIAdapter(
            client=mock_client,
            registry=registry_with_tool,
            model="gpt-4o-mini",
        )
        result = adapter.call_with_tools("Use echo tool")

        assert result == "mock_tool_response"
        call_kwargs = mock_client.chat.completions.create.call_args
        assert "tools" in call_kwargs.kwargs
        tools = call_kwargs.kwargs["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "echo"

    def test_default_model(self, registry_with_tool):
        mock_client = MagicMock()
        adapter = OpenAIAdapter(client=mock_client, registry=registry_with_tool)
        assert adapter.model == "gpt-4o-mini"

    def test_extra_kwargs_passed_through(self, registry_with_tool):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = "resp"

        adapter = OpenAIAdapter(
            client=mock_client,
            registry=registry_with_tool,
            temperature=0.5,
        )
        adapter.generate("test")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["temperature"] == 0.5


# ---------------------------------------------------------------------------
# AnthropicAdapter
# ---------------------------------------------------------------------------

class TestAnthropicAdapter:
    """Tests for the Anthropic adapter with mocked client."""

    def test_generate_calls_client(self, registry_with_tool):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = "mock_response"

        adapter = AnthropicAdapter(
            client=mock_client,
            registry=registry_with_tool,
            model="claude-3.5-sonnet-20241022",
            max_tokens=512,
        )
        result = adapter.generate("Hello")

        assert result == "mock_response"
        mock_client.messages.create.assert_called_once_with(
            model="claude-3.5-sonnet-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": "Hello"}],
        )

    def test_call_with_tools_passes_tools(self, registry_with_tool):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = "mock_tool_response"

        adapter = AnthropicAdapter(
            client=mock_client,
            registry=registry_with_tool,
        )
        result = adapter.call_with_tools("Use echo tool")

        assert result == "mock_tool_response"
        call_kwargs = mock_client.messages.create.call_args
        assert "tools" in call_kwargs.kwargs
        tools = call_kwargs.kwargs["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "echo"

    def test_default_model_and_max_tokens(self, registry_with_tool):
        mock_client = MagicMock()
        adapter = AnthropicAdapter(client=mock_client, registry=registry_with_tool)
        assert adapter.model == "claude-3.5-sonnet-20241022"
        assert adapter.max_tokens == 1024

    def test_extra_kwargs_passed_through(self, registry_with_tool):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = "resp"

        adapter = AnthropicAdapter(
            client=mock_client,
            registry=registry_with_tool,
            system="You are helpful",
        )
        adapter.generate("test")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["system"] == "You are helpful"
