from typing import Any
from .base import BaseAdapter
from corefoundry.core import registry


# you need the official OpenAI client lib installed for this file to work.


class OpenAIAdapter(BaseAdapter):
    def __init__(self, client, registry=registry, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(registry)
        self.client = client
        self.model = model
        self.extra = kwargs

    def generate(self, prompt: str) -> Any:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **self.extra,
        )
        return resp

    def call_with_tools(self, prompt: str) -> Any:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=self.registry.get_json(),
            **self.extra,
        )
        return resp
