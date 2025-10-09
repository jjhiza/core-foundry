from typing import Any
from abc import ABC, abstractmethod
from corefoundry.core import ToolRegistry


class BaseAdapter(ABC):
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    @abstractmethod
    def generate(self, prompt: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def call_with_tools(self, prompt: str) -> Any:
        raise NotImplementedError
