"""LLM Provider Adapters for CoreFoundry

This package contains adapters that integrate the CoreFoundry tool registry
with various LLM providers (OpenAI, Anthropic, etc.)

Available Adapters:
- OpenAIAdapter: For OpenAI's GPT models
- AnthropicAdapter: For Anthropic's Claude models
- BaseAdapter: Abstract base class for creating custom adapters

To use an adapter, you need to install the corresponding provider's SDK:
- OpenAI: pip install openai
- Anthropic: pip install anthropic

Or install all adapters at once:
    pip install corefoundry[adapters]
"""
