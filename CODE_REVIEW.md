# CoreFoundry — Comprehensive Code Review

**Project**: CoreFoundry v0.3.0
**Description**: A lightweight, LLM-agnostic micro-framework for AI agent tool management
**Review Date**: 2026-02-25
**Reviewer**: Automated deep review (Claude)

---

## Grade Summary

| Category              | Grade | Score |
|-----------------------|:-----:|------:|
| Code Quality          |  B+   | 88/100|
| Test Coverage         |  D    | 35/100|
| Feature Completeness  |  B    | 82/100|
| Architecture          |  A-   | 92/100|
| **Overall**           |**B-** |**74/100**|

---

## 1. Code Quality — Grade: B+

### Strengths

- **Consistent style throughout.** All Python files use 4-space indentation,
  PascalCase for classes, snake_case for functions, and proper spacing.
  No linter is configured, yet the code reads as if one were enforced.

- **Comprehensive type annotations.** Every public function and method carries
  parameter and return type hints. `from __future__ import annotations` is used
  for forward-reference support. `Optional`, `Dict`, `List`, and `Callable` are
  applied correctly.

- **Strong Pydantic usage.** Schema validation is done at registration time via
  `ToolProperty`, `InputSchema`, and `ToolDefinition` models. The
  `model_validator` on `ToolProperty` enforces that `items` is present when
  `type == "array"` — a real-world requirement for Gemini/OpenAI function
  definitions.

- **Thorough docstrings.** All public classes and methods have docstrings with
  Args/Returns/Raises sections and inline examples. Module-level docstrings
  are present in key files.

- **Clean error handling.** Exceptions are specific (`ValueError`,
  `ImportError`, `KeyError`, `RuntimeError`) and include context in messages.
  Pydantic `ValidationError` is caught and re-raised with the tool name for
  debuggability.

- **No hardcoded secrets.** API clients are injected, not constructed. The
  `.gitignore` properly excludes `.env` and `.envrc`.

### Issues Found

1. **Bug: wrong variable in error message** (`corefoundry/core.py:221`)

   ```python
   tool = self._tools.get(name)
   if not tool:
       raise KeyError(f"Tool '{tool}' not found")  # prints "Tool 'None' not found"
   ```

   Should be `f"Tool '{name}' not found"`. Low severity but will confuse
   callers trying to debug a missing-tool error.

2. **Deprecated Pydantic method** (`corefoundry/core.py:199`)

   ```python
   "input_schema": t.input_schema.dict(exclude_none=True),
   ```

   In Pydantic v2, `.dict()` is deprecated in favor of `.model_dump()`. This
   works today but will emit deprecation warnings under strict settings and
   will break when Pydantic eventually removes the shim.

3. **No linter or formatter configured.** There is no `ruff.toml`, `.flake8`,
   `pyproject.toml [tool.ruff]`, or `black` config. The code is clean by
   convention alone, but this is fragile for external contributions.

4. **No upper-bound on dependency versions.** `pydantic>=2.0` is fully
   open-ended. A future Pydantic 4.x with breaking changes would be silently
   accepted. A constraint like `pydantic>=2.0,<4.0` is safer for a published
   package.

5. **`__pycache__` directories committed.** Despite `.gitignore` listing
   `__pycache__/`, several `*.cpython-311.pyc` files are tracked. These should
   be purged from history.

---

## 2. Test Coverage — Grade: D

### What Exists

The project has exactly **two test files** containing **two test functions**
totaling 19 lines of test code:

| File                   | Tests | Lines | What It Tests                         |
|------------------------|:-----:|------:|---------------------------------------|
| `tests/test_registry.py` | 1  |    15 | Register a tool and call it via `get_callable` |
| `tests/test_agent.py`    | 1  |    19 | Register a tool and call it via `Agent.call_tool` |

### What Is Missing

The following areas have **zero test coverage**:

- **Schema validation** — no tests for `ToolProperty`, `InputSchema`, array
  `items` enforcement, enum handling, nested object schemas, or Pydantic
  validation error paths.
- **Error paths** — no tests for duplicate registration, missing tool lookup,
  tool with no callable, invalid schema, or bad package in `autodiscover()`.
- **`autodiscover()`** — no test for package discovery, module vs. package
  handling, or `ImportError` behavior.
- **`get_json()` / `get_all()` / `list_names()`** — no serialization tests.
- **Adapters** — `OpenAIAdapter`, `AnthropicAdapter`, and `BaseAdapter` have
  zero tests. No mocks of the OpenAI or Anthropic clients.
- **`Agent` class** — only the `call_tool` happy path is tested; `tool_names`,
  `available_tools_json`, and `auto_tools_pkg` are untested.
- **Edge cases** — empty registry, tools with no `input_schema`, async tool
  registration, tools with complex nested schemas.
- **No test configuration.** No `conftest.py`, no `pytest.ini`, no coverage
  reporting, no CI integration.
- **No test isolation.** Both tests register tools into the global registry
  using `__test_` prefixed names, but never clean up. Running tests in
  different orders could cause "already registered" failures.

### Impact

With only two happy-path tests covering roughly 10% of the source code by
line count and none of the error/edge paths, there is significant regression
risk for any future changes.

---

## 3. Feature Completeness — Grade: B

### Implemented Features (Working)

| Feature                        | Status | Notes                                    |
|--------------------------------|:------:|------------------------------------------|
| Decorator-based tool registration | Done | Clean API, schema validation at register time |
| Auto-discovery from packages   | Done   | `autodiscover()` via `pkgutil`           |
| JSON export for LLM providers  | Done   | Anthropic-native format; adapters convert |
| Runtime tool execution         | Done   | `call_tool()` with kwargs dispatch       |
| Pydantic schema validation     | Done   | `ToolProperty`, `InputSchema`, validators |
| OpenAI adapter                 | Done   | `generate()` and `call_with_tools()`     |
| Anthropic adapter              | Done   | `generate()` and `call_with_tools()`     |
| Abstract adapter base class    | Done   | Enforces `generate` / `call_with_tools` contract |
| Async tool support             | Done   | By design — callables can be coroutines  |
| Example project                | Done   | `examples/demo.py` + `my_tools` package  |
| Comprehensive README           | Done   | Security section, API reference, examples |

### Not Yet Implemented (from Roadmap / Expected)

| Feature                             | Status   | Impact                                |
|-------------------------------------|:--------:|---------------------------------------|
| Runtime input validation            | Missing  | Tools receive unvalidated kwargs      |
| Additional LLM adapters             | Missing  | No local model / Gemini / Cohere adapters |
| Tool deregistration / registry reset| Missing  | No way to remove tools once registered |
| Conversation/message management     | N/A      | Intentionally out of scope per philosophy |
| Agent orchestration                 | N/A      | Intentionally out of scope            |

### Observations

- The framework delivers on its stated micro-framework promise: clean tool
  registration, schema validation, JSON serialization, and provider adapters.
- Runtime input validation is the most impactful missing feature. Currently,
  `call_tool()` passes kwargs directly to the function with no schema check,
  meaning invalid inputs only fail at the Python function level, not at the
  schema level.
- The inability to deregister or reset the registry limits testability and
  makes multi-phase applications harder to build.
- The adapter `call_with_tools()` methods only handle a single user message
  with no conversation history, which limits real-world multi-turn usage. This
  is acceptable for a micro-framework but worth noting.

---

## 4. Architecture — Grade: A-

### Overall Pattern

CoreFoundry follows a **Registry + Adapter pattern** with clear layered
boundaries:

```
┌──────────────────────────────────────────┐
│  User Tool Functions (@registry.register)│
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│  Core Layer (corefoundry/)               │
│  - ToolRegistry: registration, storage   │
│  - Pydantic models: schema validation    │
│  - Agent: convenience wrapper            │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│  Adapter Layer (agent_adapters/)         │
│  - BaseAdapter: abstract interface       │
│  - OpenAIAdapter: OpenAI integration     │
│  - AnthropicAdapter: Anthropic integ.    │
└──────────────────────────────────────────┘
```

### Strengths

- **Strong separation of concerns.** The core package is entirely LLM-agnostic.
  Adapters depend on core but core never imports adapters. Tool functions are
  decoupled from both.

- **Minimal dependency graph.** Core requires only Pydantic. Adapters are
  optional extras. This is ideal for a framework meant to be embedded.

- **Composition over inheritance.** `Agent` composes `ToolRegistry` rather than
  extending it. Adapters compose the registry. Only `BaseAdapter` uses
  inheritance, and it's a clean ABC.

- **Dependency injection.** Adapters accept a `client` and `registry` via
  constructor. This makes them testable (you can pass mock clients) and
  configurable.

- **Single Responsibility Principle.** Each class has one job: `ToolProperty`
  validates a property, `InputSchema` validates a schema, `ToolDefinition`
  holds tool metadata, `ToolRegistry` manages the collection, `Agent` provides
  a user-facing API, adapters handle provider specifics.

- **Intentional scope boundaries.** The README explicitly states what the
  framework does NOT do (orchestration, conversation management, agent runtime).
  This is mature design thinking.

### Weaknesses

- **Global mutable singleton.** `registry = ToolRegistry()` at module level
  (core.py:236) is shared across all imports. The README documents this
  trade-off, but it creates challenges for testing (no reset method), multi-
  tenancy (all agents share tools), and parallel test execution.

- **Agent is tightly coupled to the global registry.** `Agent.__init__` always
  uses the module-level `registry` — it doesn't accept a custom registry
  instance. This means you cannot create two Agents with different tool sets
  in the same process.

- **Adapter `generate` vs `call_with_tools` duplication.** Both OpenAI and
  Anthropic adapters duplicate 90% of the code between `generate()` and
  `call_with_tools()`, differing only by the presence of `tools=`. A private
  helper like `_create(prompt, tools=None)` would reduce this.

- **No middleware/hook system.** There is no way to intercept tool calls for
  logging, authorization, rate limiting, or input validation without modifying
  tool functions directly. A simple pre/post-call hook would add significant
  value.

---

## Detailed Findings

### Bugs

| # | Severity | Location              | Description                                     |
|---|----------|-----------------------|-------------------------------------------------|
| 1 | Low      | `core.py:221`         | Error message uses `{tool}` (None) instead of `{name}` |

### Code Smells

| # | Severity | Location              | Description                                     |
|---|----------|-----------------------|-------------------------------------------------|
| 1 | Low      | `core.py:199`         | `.dict()` deprecated in Pydantic v2; use `.model_dump()` |
| 2 | Low      | `core.py:170-172`     | Silent return when autodiscover receives a module instead of package |
| 3 | Info     | `openai_adapter.py:60`| `get_json()` returns Anthropic-format schemas; OpenAI adapter passes them as-is without converting to OpenAI's `functions` format |

### Security Notes

All documented transparently in the README — no hidden risks:

- Global registry is shared (documented)
- `autodiscover()` executes arbitrary code from packages (documented)
- No runtime input validation (documented, recommended in tool functions)
- No multi-tenant isolation (documented, application's responsibility)

### Documentation Quality

The README is **excellent** — one of the project's strongest assets:

- Clear problem statement and motivation
- Before/after code comparison
- Quick start guide with 3 progressive steps
- Security considerations section with concrete examples
- API reference for all public methods
- Project structure diagram
- Development setup instructions
- Roadmap with checked/unchecked items

---

## Recommendations (Priority Order)

### High Priority

1. **Add tests.** Target at minimum: schema validation (valid and invalid),
   error paths (duplicate registration, missing tool, bad autodiscover input),
   `get_json()` serialization, and adapter behavior with mocked clients. A
   `conftest.py` with a fresh registry fixture would solve the isolation
   problem.

2. **Fix the error message bug** at `core.py:221` — change `{tool}` to
   `{name}`.

3. **Add a `clear()` or `reset()` method** to `ToolRegistry` for testability
   and lifecycle management.

### Medium Priority

4. **Replace `.dict()` with `.model_dump()`** to stay current with Pydantic v2.

5. **Allow `Agent` to accept a custom `ToolRegistry`** instead of always using
   the global singleton. This enables isolated tool sets per agent.

6. **Add linter configuration** (ruff or flake8 + black) to `pyproject.toml`
   and optionally a pre-commit config.

7. **Add upper bounds to dependency versions** (e.g., `pydantic>=2.0,<4.0`).

### Low Priority

8. **Purge `__pycache__` from git history** and verify `.gitignore` is working.

9. **Consider a pre/post-call hook system** for logging, auth, and validation.

10. **Add CI/CD** (GitHub Actions) for automated testing on push/PR.

---

## Files Reviewed

| File                                    | Lines | Role                        |
|-----------------------------------------|------:|-----------------------------|
| `corefoundry/__init__.py`               |     6 | Public API exports          |
| `corefoundry/core.py`                   |   237 | Registry, models, validation|
| `corefoundry/agent.py`                  |    53 | Agent wrapper               |
| `agent_adapters/__init__.py`            |    17 | Adapter package docstring   |
| `agent_adapters/base.py`               |    44 | Abstract adapter base class |
| `agent_adapters/openai_adapter.py`      |    63 | OpenAI integration          |
| `agent_adapters/anthropic_adapter.py`   |    74 | Anthropic integration       |
| `examples/demo.py`                      |     9 | Demo script                 |
| `examples/my_tools/text_tools.py`       |    27 | Example tool definitions    |
| `tests/test_registry.py`               |    15 | Registry test               |
| `tests/test_agent.py`                  |    19 | Agent test                  |
| `pyproject.toml`                        |    38 | Package configuration       |
| `README.md`                             |   488 | Documentation               |
| `.gitignore`                            |    28 | Git exclusions              |
| **Total**                               |**1118**| **12 source + 2 config**   |

---

## Conclusion

CoreFoundry is a well-architected micro-framework with clean code, strong
typing, and excellent documentation. The architecture earns near top marks for
its clear separation of concerns, minimal dependencies, and intentional scope.
Code quality is solid with only minor issues (one bug, one deprecation).

The critical weakness is test coverage: two happy-path tests covering ~10% of
the code leave the project vulnerable to regressions. Investing in a proper
test suite would elevate the overall grade from B- to a solid A-range project.

For a v0.3.0 beta, this is a promising foundation. The design decisions are
sound, the documentation is thorough, and the codebase is small enough that
the test gap can be closed quickly.
