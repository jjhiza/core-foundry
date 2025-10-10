# CoreFoundry

A lightweight, LLM-agnostic micro-framework for AI agent tool management.

CoreFoundry eliminates the boilerplate from building AI agents with tools. Define tools with a simple decorator, auto-discover them from packages, and let CoreFoundry handle all the schema management and serialization. As a micro-framework, CoreFoundry focuses solely on tool definition and management - not agent orchestration.

## Features

- **LLM-Agnostic**: Works with any LLM provider (OpenAI, Anthropic, local models, etc.)
- **Decorator-Based Registration**: Simple `@registry.register` decorator for tool definitions
- **Auto-Discovery**: Automatically discover and register tools from Python packages
- **Type-Safe**: Built on Pydantic for schema validation
- **Extensible**: Easy-to-implement adapter pattern for any LLM provider

## Important: Global Registry

⚠️ **CoreFoundry uses a global tool registry.** All Agent instances share the same registered tools. This is fine for single-user applications, but requires consideration in multi-tenant environments. [Read more about registry isolation →](#global-registry)

## Why CoreFoundry?

**Problem**: Building AI agents with tools requires tons of repetitive boilerplate code.

Every tool needs:

- A function implementation
- A separate JSON schema definition
- Manual wiring between tool calls and functions
- Serialization logic for LLM providers
- Discovery and registration code

**Without CoreFoundry:**

```python
# Define the schema separately
tool_schema = {
    "type": "function",
    "function": {
        "name": "to_uppercase",
        "description": "Convert text to uppercase",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "input text"}
            },
            "required": ["text"]
        }
    }
}

# Implement the function
def to_uppercase(text: str) -> str:
    return text.upper()

# Manually map tool names to functions
tool_map = {"to_uppercase": to_uppercase}

# Repeat for every tool...
```

**With CoreFoundry:**

```python
@registry.register(
    description="Convert text to uppercase",
    input_schema={
        "properties": {"text": {"type": "string", "description": "input text"}},
        "required": ["text"],
    }
)
def to_uppercase(text: str) -> str:
    return text.upper()
```

**That's it.** CoreFoundry handles:

- ✅ Schema validation with Pydantic
- ✅ Automatic tool discovery
- ✅ JSON serialization for any LLM
- ✅ Runtime tool execution
- ✅ Clean separation of concerns

**CoreFoundry is a micro-framework** - it handles tool management, not agent orchestration. You stay in control of your application architecture while CoreFoundry eliminates the tool definition boilerplate.

And it works with **any LLM provider** - OpenAI, Anthropic, local models, or your own custom integration.

## Design Philosophy

CoreFoundry is intentionally minimal:

- **Focused scope**: Tool definition and management only - no orchestration, no conversation handling, no agent runtime
- **You stay in control**: No hidden magic, no architectural constraints, no opinionated workflows
- **Composable**: Works alongside any agent framework (LangChain, CrewAI, custom solutions) or standalone
- **Reduces friction, not flexibility**: Eliminates boilerplate while letting you build agents your way

If you need full agent orchestration, consider frameworks like LangChain or MCP. If you just want to define tools without the ceremony, CoreFoundry is for you.

## Installation

### Basic Installation

```bash
uv pip install corefoundry
```

### With OpenAI Adapter

```bash
uv pip install corefoundry[adapters]
```

> **Note**: CoreFoundry works with any package manager. If you prefer pip: `pip install corefoundry`

## Quick Start

### 1. Define Your Tools

Create a Python module with your tools:

```python
# my_tools/text_tools.py
from corefoundry import registry

@registry.register(
    description="Convert text to uppercase",
    input_schema={
        "properties": {"text": {"type": "string", "description": "input text"}},
        "required": ["text"],
    },
)
def to_uppercase(text: str) -> str:
    return text.upper()

@registry.register(
    description="Count words in text",
    input_schema={
        "properties": {"text": {"type": "string"}},
        "required": ["text"]
    },
)
def count_words(text: str) -> int:
    return len(text.split())
```

### 2. Create an Agent

```python
from corefoundry import Agent

# Create agent and auto-discover tools
agent = Agent(
    name="MyAgent",
    description="A helpful text processing agent",
    auto_tools_pkg="my_tools"
)

# View available tools
print(agent.tool_names())
# ['to_uppercase', 'count_words']

# Get tool definitions as JSON (for LLM consumption)
print(agent.available_tools_json())

# Call a tool directly
result = agent.call_tool("to_uppercase", text="hello world")
print(result)  # "HELLO WORLD"
```

### 3. Use with an LLM (Optional)

```python
from agent_adapters.openai_adapter import OpenAIAdapter
from openai import OpenAI

client = OpenAI(api_key="your-api-key")
adapter = OpenAIAdapter(client=client, model="gpt-4o-mini")

# The adapter can now use your registered tools
response = adapter.call_with_tools("Convert 'hello world' to uppercase")
```

## Core Concepts

### Tool Registry

The registry is a global singleton that manages tool definitions:

```python
from corefoundry import registry

@registry.register(
    name="custom_name",  # Optional: defaults to function name
    description="What this tool does",
    input_schema={
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer"}
        },
        "required": ["param1"]
    }
)
def my_tool(param1: str, param2: int = 0):
    return f"{param1}: {param2}"
```

### Agent

The `Agent` class provides a convenient wrapper around the registry:

- **Auto-discovery**: Automatically imports and registers tools from a package
- **JSON Export**: Exports tool definitions in LLM-compatible format
- **Tool Execution**: Call tools by name at runtime

```python
agent = Agent(
    name="MyAgent",
    description="Agent description",
    auto_tools_pkg="my_tools"  # Optional: auto-discover tools
)
```

### Async Tools

CoreFoundry supports both synchronous and asynchronous tools. You're responsible for handling async execution in your application.

**Registering async tools:**

```python
import httpx
from corefoundry import registry

@registry.register(
    description="Fetch content from a URL",
    input_schema={
        "properties": {"url": {"type": "string"}},
        "required": ["url"]
    }
)
async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

**Using async tools:**

```python
import asyncio
from corefoundry import Agent

agent = Agent("MyAgent", auto_tools_pkg="my_tools")

# Option 1: Await directly in async context
async def main():
    result = await agent.call_tool("fetch_url", url="https://example.com")
    print(result)

asyncio.run(main())

# Option 2: Run in event loop
result = asyncio.run(agent.call_tool("fetch_url", url="https://example.com"))
```

**Note:** `call_tool()` returns a coroutine when calling async tools. You must `await` it or run it in an event loop. CoreFoundry doesn't automatically handle async execution - that's your application's responsibility.

### Adapters

Adapters integrate the registry with specific LLM providers. CoreFoundry includes an OpenAI adapter, and you can create your own:

```python
from agent_adapters.base import BaseAdapter
from corefoundry import registry

class MyLLMAdapter(BaseAdapter):
    def __init__(self, client, registry=registry):
        super().__init__(registry)
        self.client = client

    def generate(self, prompt: str):
        # Implement LLM call
        pass

    def call_with_tools(self, prompt: str):
        # Implement LLM call with tools
        tools = self.registry.get_json()
        # Pass tools to your LLM provider
        pass
```

## Input Schema Format

CoreFoundry uses JSON Schema for tool input validation:

```python
input_schema = {
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the file"
        },
        "mode": {
            "type": "string",
            "description": "Read mode",
            "enum": ["text", "binary"]
        },
        "max_lines": {
            "type": "integer",
            "description": "Maximum lines to read"
        }
    },
    "required": ["file_path"]
}
```

Supported types: `string`, `integer`, `number`, `boolean`, `array`, `object`

## API Reference

### `registry.register(name=None, description=None, input_schema=None)`

Decorator to register a function as a tool.

**Parameters:**

- `name` (str, optional): Tool name (defaults to function name)
- `description` (str, optional): Tool description (defaults to docstring)
- `input_schema` (dict, optional): JSON Schema for tool inputs

### `Agent(name, description="", auto_tools_pkg=None)`

Create a new agent.

**Parameters:**

- `name` (str): Agent name
- `description` (str): Agent description
- `auto_tools_pkg` (str, optional): Package to auto-discover tools from

**Methods:**

- `tool_names()`: List all registered tool names
- `available_tools_json()`: Get tool definitions as JSON string
- `call_tool(name, **kwargs)`: Execute a tool by name

### `registry.autodiscover(package_name)`

Discover and register tools from a package.

**Parameters:**

- `package_name` (str): Fully qualified package name (e.g., "my_app.tools")

**Security Note:** Only use with trusted packages. This imports and executes code.

## Security Considerations

### Important Security Notes:

1. **Trusted Tools Only**: Only register tools from trusted sources. Registered tools have full Python execution privileges.

2. **Auto-Discovery Safety**: The `autodiscover()` method imports Python modules. Only use with trusted package names:

   ```python
   # Safe: your own package
   agent = Agent(auto_tools_pkg="my_app.tools")

   # Unsafe: user-controlled input
   pkg = input("Enter package: ")  # DON'T DO THIS
   agent = Agent(auto_tools_pkg=pkg)
   ```

3. **Global Registry**: The registry is a global singleton. In multi-tenant applications, tools are shared across all Agent instances.

   **What this means:**

   ```python
   # Agent A registers admin tools
   agent_a = Agent("Admin", auto_tools_pkg="admin_tools")
   # Tools: delete_file, restart_server, etc.

   # Agent B in the same process can also access admin tools
   agent_b = Agent("Guest", auto_tools_pkg="guest_tools")
   # agent_b.call_tool("delete_file", ...) will work!
   ```

   **If you're building multi-tenant systems, consider:**
   - Using separate processes for different tenants/users
   - Deploying isolated containers per tenant
   - Implementing authorization checks within tool functions
   - Being very careful about what gets registered globally

   **This is by design** - CoreFoundry reduces boilerplate, not orchestration. Multi-tenant isolation is the application's responsibility.

4. **Input Validation**: While CoreFoundry validates schema structure, it does NOT automatically validate tool inputs at runtime. Implement input validation in your tool functions:

   ```python
   @registry.register(...)
   def read_file(file_path: str):
       # Validate inputs in your tool
       if not os.path.exists(file_path):
           raise ValueError("File not found")
       if not file_path.startswith("/allowed/path/"):
           raise ValueError("Access denied")
       # ... safe file reading
   ```

5. **LLM-Generated Tool Calls**: When using with LLMs, remember that LLMs can be prompted to call tools in unexpected ways. Implement appropriate safeguards in tool implementations.

## Project Structure

```
├── corefoundry/                       # core package (LLM-agnostic)
│   ├── __init__.py
│   ├── core.py                        # registry, models, autodiscover
│   └── agent.py                       # agent wrapper / executor
│
├── agent_adapters/                    # optional adapters (separate package)
│   ├── __init__.py
│   ├── base.py
│   └── openai_adapter.py
│
├── examples/
│   ├── my_tools/
│   │   ├── __init__.py
│   │   └── text_tools.py
│   └── demo.py
│
├── tests/
│   ├── test_registry.py
│   └── test_agent.py
│
├── pyproject.toml
├── README.md
└── LICENSE
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/jjhiza/core-foundry.git
cd corefoundry

# Install in editable mode (uv handles virtual environment automatically)
uv pip install -e .

# Install with optional dependencies
uv pip install -e ".[adapters]"
```

### Running Tests

```bash
pytest tests/
```

### Running Examples

```bash
python examples/demo.py
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Roadmap

- [ ] Additional LLM adapters (local models, etc.)
  - [x] OpenAI adapter
  - [x] Anthropic adapter
- [ ] Runtime input validation against schemas

## Support

- **Issues**: https://github.com/jjhiza/corefoundry/issues
- **Discussions**: https://github.com/jjhiza/corefoundry/discussions
