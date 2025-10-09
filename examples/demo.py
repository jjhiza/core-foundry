from corefoundry.agent import Agent

agent = Agent(name="DemoAgent", auto_tools_pkg="examples.my_tools")
print(f"Available tools: {agent.tool_names()}")
print(f"Tool JSON: {agent.available_tools_json()}")

# call a tool
result = agent.call_tool("to_uppercase", text="hello world!")
print(f"Result: {result}")
