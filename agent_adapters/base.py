from typing import Any
from abc import ABC, abstractmethod
from corefoundry.core import ToolRegistry


class BaseAdapter(ABC):
    """Abstract base class for LLM provider adapters

    Adapters integrate the CoreFoundry tool registry with specific LLM providers

    (OpenAI, Anthropic, etc.), handling provider-specific API formats
    """

    def __init__(self, registry: ToolRegistry):
        """Initialize the adapter with a tool registry

        Args:
            registry: ToolRegistry instance containing registered tools
        """
        self.registry = registry

    @abstractmethod
    def generate(self, prompt: str) -> Any:
        """Generate a response from the LLM without tool use

        Args:
            prompt: User prompt to send to the LLM

        Returns:
            Provider-specific response object
        """
        raise NotImplementedError

    @abstractmethod
    def call_with_tools(self, prompt: str) -> Any:
        """Generate a response from the LLM with tool use enabled

        Args:
            prompt: User prompt to send to the LLM

        Returns:
            Provider-specific response object with potential tool calls
        """
        raise NotImplementedError
