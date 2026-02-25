"""Shared fixtures for CoreFoundry tests."""

import pytest
from corefoundry.core import ToolRegistry


@pytest.fixture()
def fresh_registry():
    """Provide a fresh, isolated ToolRegistry for each test."""
    return ToolRegistry()
