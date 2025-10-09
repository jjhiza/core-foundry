from typing import Any
from .base import BaseAdapter
from corefoundry.core import registry

# You need the official Anthropic client lib installed for this file to work.


class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic's Claude API

    Integrates CoreFoundry tools with Claude models (Opus, Sonnet, Haiku)
    """

    def __init__(
        self,
        client,
        registry=registry,
        model: str = "claude-3.5-sonnet-20241022",
        max_tokens: int = 1024,
        **kwargs,
    ):
        """Initialize Anthropic adapter

        Args:
            client: Anthropic client instance

            registry: ToolRegistry to use (defaults to global registry)

            model: Claude model name (default: "claude-3.5-sonnet-20241022")

            max_tokens: Maximum tokens in response (default: 1024)

            **kwargs: Additional parameters to pass to Anthropic API calls
        """
        super().__init__(registry)
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.extra = kwargs

    def generate(self, prompt: str) -> Any:
        """Generate a completion without tools

        Args:
            prompt: User prompt

        Returns:
            Anthropic Message response object
        """
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **self.extra,
        )
        return resp

    def call_with_tools(self, prompt: str) -> Any:
        """Generate a completion with tools enabled

        Args:
            prompt: User prompt

        Returns:
            Anthropic Message response object (may include tool use blocks)
        """
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            tools=self.registry.get_json(),
            **self.extra,
        )
        return resp
