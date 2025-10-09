from corefoundry.agent import Agent
from corefoundry.core import registry


def test_agent_call():
    @registry.register(
        name="__test_add",
        description="add",
        input_schema={
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    )
    def add(a: int, b: int):
        return a + b

    agent = Agent("t")
    res = agent.call_tool("__test_add", a=2, b=3)
    assert res == 5
