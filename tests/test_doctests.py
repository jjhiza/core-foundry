"""Run doctests embedded in the corefoundry.core module."""

import doctest
import corefoundry.core


def test_core_doctests():
    results = doctest.testmod(corefoundry.core, verbose=False)
    assert results.failed == 0, f"{results.failed} doctest(s) failed"
