"""Comprehensive unit tests for the Agent class."""

import json
import pytest

from corefoundry.core import ToolRegistry
from corefoundry.agent import Agent


@pytest.fixture()
def agent_with_tools():
    """Create an Agent backed by a fresh registry with two tools."""
    reg = ToolRegistry()

    @reg.register(
        name="upper",
        description="Uppercase text",
        input_schema={
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    )
    def upper(text: str):
        return text.upper()

    @reg.register(
        name="add",
        description="Add two numbers",
        input_schema={
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )
    def add(a: int, b: int):
        return a + b

    agent = Agent(name="TestAgent", description="test agent")
    # Swap in our isolated registry
    agent._registry = reg
    return agent


class TestAgentInit:
    """Tests for Agent construction."""

    def test_agent_name_and_description(self):
        agent = Agent(name="MyAgent", description="does things")
        assert agent.name == "MyAgent"
        assert agent.description == "does things"

    def test_agent_default_description(self):
        agent = Agent(name="A")
        assert agent.description == ""


class TestAgentToolNames:
    """Tests for Agent.tool_names()."""

    def test_tool_names_returns_registered_tools(self, agent_with_tools):
        names = agent_with_tools.tool_names()
        assert set(names) == {"upper", "add"}

    def test_tool_names_empty_registry(self):
        agent = Agent(name="Empty")
        agent._registry = ToolRegistry()
        assert agent.tool_names() == []


class TestAgentCallTool:
    """Tests for Agent.call_tool()."""

    def test_call_tool_upper(self, agent_with_tools):
        result = agent_with_tools.call_tool("upper", text="hello")
        assert result == "HELLO"

    def test_call_tool_add(self, agent_with_tools):
        result = agent_with_tools.call_tool("add", a=10, b=20)
        assert result == 30

    def test_call_tool_missing_raises_keyerror(self, agent_with_tools):
        with pytest.raises(KeyError):
            agent_with_tools.call_tool("nonexistent")


class TestAgentAvailableToolsJson:
    """Tests for Agent.available_tools_json()."""

    def test_returns_valid_json(self, agent_with_tools):
        raw = agent_with_tools.available_tools_json()
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_json_contains_expected_tool_names(self, agent_with_tools):
        parsed = json.loads(agent_with_tools.available_tools_json())
        names = {t["name"] for t in parsed}
        assert names == {"upper", "add"}

    def test_json_tool_has_required_keys(self, agent_with_tools):
        parsed = json.loads(agent_with_tools.available_tools_json())
        for tool in parsed:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
