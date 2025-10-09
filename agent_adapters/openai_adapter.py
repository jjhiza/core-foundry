from typing import Any
from .base import BaseAdapter
from corefoundry.core import registry


# You need the official OpenAI client lib installed for this file to work.


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI's chat completion API

    Integrates CoreFoundry tools with OpenAI models like GPT-4 and GPT-3.5
    """

    def __init__(self, client, registry=registry, model: str = "gpt-4o-mini", **kwargs):
        """Initialize OpenAI adapter

        Args:
            client: OpenAI client instance

            registry: ToolRegistry to use (defaults to global registry)

            model: OpenAI model name (default: "gpt-4o-mini")

            **kwargs: Additional parameters to pass to OpenAI API calls
        """
        super().__init__(registry)
        self.client = client
        self.model = model
        self.extra = kwargs

    def generate(self, prompt: str) -> Any:
        """Generate a completion without tools

        Args:
            prompt: User prompt

        Returns:
            OpenAI ChatCompletion response object
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **self.extra,
        )
        return resp

    def call_with_tools(self, prompt: str) -> Any:
        """Generate a completion with tools enabled

        Args:
            prompt: User prompt

        Returns:
            OpenAI ChatCompletion response object (may include tool calls)
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=self.registry.get_json(),
            **self.extra,
        )
        return resp
