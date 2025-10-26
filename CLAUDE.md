# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLLM is a bash-centric command-line interface for interacting with large language models across 100+ providers. The project provides a unified Python API and CLI for chaining LLM calls using familiar bash piping techniques.

**Key Design Principles:**
- Provider abstraction via LiteLLM (OpenAI-compatible interface)
- Bash-first design for piping and scripting workflows
- Modern Python packaging with uv for performance

## Architecture

### Core Components

**`src/cllm/client.py`** - LLMClient class
- Wraps LiteLLM's `completion()` and `acompletion()` functions
- Provides simplified interface: string prompts auto-convert to message format
- Supports streaming, async, temperature, max_tokens
- Returns text by default; `raw_response=True` for full API response
- Key method: `complete(model, messages, stream=False, temperature=None, max_tokens=None, **kwargs)`

**`src/cllm/cli.py`** - Command-line interface
- Entry point: `cllm` command registered in `pyproject.toml`
- Reads from stdin (for piping) or command-line arguments
- Supports `--stream`, `--temperature`, `--max-tokens`, `--raw` flags
- Default model: `gpt-3.5-turbo`

**Provider Abstraction (ADR-0002)**
- Uses LiteLLM Python SDK for multi-provider support
- Switching providers = changing model name only (e.g., `"gpt-4"` → `"claude-3-opus-20240229"`)
- All responses follow OpenAI format: `response['choices'][0]['message']['content']`
- API keys via environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.

### Package Structure

```
src/cllm/          # Main package (configured in pyproject.toml)
  __init__.py      # Exports LLMClient
  client.py        # Core LLMClient implementation
  cli.py           # CLI entry point
tests/             # Test suite (pytest)
  test_client.py   # LLMClient tests (mock-based)
examples/          # Usage examples
  basic_usage.py   # Multi-provider examples
  async_usage.py   # Async patterns
  provider_comparison.py
docs/decisions/    # Architecture Decision Records (ADRs)
```

## Development Commands

### Package Management (uv - ADR-0001)

**Install dependencies:**
```bash
uv sync
```

**Add new dependency:**
```bash
uv add <package>
```

**Run tests:**
```bash
uv run pytest
```

**Run specific test:**
```bash
uv run pytest tests/test_client.py::TestLLMClient::test_complete_with_string_message -v
```

**Run CLI locally:**
```bash
uv run cllm "Your prompt here" --model gpt-4
```

**Build package:**
```bash
uv build
```

### Testing Strategy

- Use `@patch('cllm.client.completion')` to mock LiteLLM calls
- Tests verify the abstraction interface, not LiteLLM internals
- Mock response format: `{"choices": [{"message": {"content": "..."}}]}`
- For streaming tests: `iter([{"choices": [{"delta": {"content": "..."}}]}])`
- All 11 tests in `test_client.py` should pass

### Git Workflow

- Main branch: `main`
- Use conventional commits (see `.claude/skills/conventional-commit/`)
- ADR skill available: `/adr` command creates architecture decision records

## Key Architectural Decisions

### ADR-0001: Use uv as Package Manager
- **Why:** 10-100x faster than pip; replaces pip, pip-tools, poetry, pyenv, virtualenv
- **Commands:** Use `uv add`, `uv sync`, `uv run` instead of pip/poetry
- **Installation:** `uv.lock` provides reproducible builds

### ADR-0002: Use LiteLLM for LLM Provider Abstraction
- **Why:** Unified OpenAI-compatible interface for 100+ providers
- **Core principle:** Same code works across all providers (just change model name)
- **Streaming:** Use `stream=True` parameter
- **Async:** Use `client.acomplete()` instead of `client.complete()`
- **Documentation:** https://docs.litellm.ai/docs/

**Example - Provider Switching:**
```python
from cllm import LLMClient
client = LLMClient()

# OpenAI
response = client.complete("gpt-4", "What is 2+2?")

# Anthropic (identical code)
response = client.complete("claude-3-opus-20240229", "What is 2+2?")

# Google (identical code)
response = client.complete("gemini-pro", "What is 2+2?")
```

## API Key Configuration

Set environment variables following LiteLLM conventions:
- `OPENAI_API_KEY="sk-..."`
- `ANTHROPIC_API_KEY="sk-ant-..."`
- `GOOGLE_API_KEY="..."`
- `GROQ_API_KEY="gsk_..."`

See: https://docs.litellm.ai/docs/providers

## Adding New Features

When adding LLM-related functionality:
1. **Always use `litellm.completion()`** instead of direct provider SDKs
2. **Test with multiple providers** to verify abstraction works
3. **Update examples/** if adding new CLI flags or API methods
4. **Follow existing patterns** in `client.py` (string-to-messages conversion, response extraction)

## Code Style

- Python 3.8+ compatibility
- Type hints for public methods
- Docstrings following Google style
- Mock external API calls in tests
- Keep CLI bash-friendly (support stdin piping)

## Important Notes

- **Do not add direct provider SDKs** (openai, anthropic, etc.) - use LiteLLM abstraction
- **Streaming responses** need special handling: extract from `chunk['choices'][0]['delta']['content']`
- **Entry point** is registered in `pyproject.toml` under `[project.scripts]`
- **Package layout** uses modern `src/` structure with hatchling backend
