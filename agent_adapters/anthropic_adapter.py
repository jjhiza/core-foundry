from typing import Any
from .base import BaseAdapter
from corefoundry.core import registry

# You need the official Anthropic
# client lib installed for this file to
# work.


class AnthropicAdapter(BaseAdapter):
    def __init__(
        self,
        client,
        registry=registry,
        model: str = "claude-3.5-sonnet-20241022",
        max_tokens: int = 1024,
        **kwargs,
    ):
        super().__init__(registry)
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.extra = kwargs

    def generate(self, prompt: str) -> Any:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **self.extra,
        )
        return resp

    def call_with_tools(self, prompt: str) -> Any:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            tools=self.registry.get_json(),
            **self.extra,
        )
        return resp
