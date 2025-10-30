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
- Supports `--stream`, `--temperature`, `--max-tokens`, `--raw`, `--config`, `--show-config` flags
- Conversation flags: `--conversation`, `--list-conversations`, `--show-conversation`, `--delete-conversation`
- Path override: `--cllm-path` flag (see ADR-0016)
- Default model: `gpt-3.5-turbo`
- Loads configuration from Cllmfile.yml (see ADR-0003, ADR-0016)
- Default behavior: stateless (no conversation saved unless `--conversation` flag used)

**`src/cllm/conversation.py`** - Conversation management (ADR-0007, ADR-0016, ADR-0017)

- `Conversation` dataclass: Holds conversation data (id, model, messages, metadata)
- `ConversationManager` class: Handles CRUD operations for conversations
- Storage precedence (ADR-0017):
  1. CLI flag: `--conversations-path` (highest)
  2. Environment variable: `CLLM_CONVERSATIONS_PATH`
  3. Configuration file: `conversations_path` in Cllmfile.yml
  4. Custom .cllm path: `<cllm_path>/conversations/` (if `--cllm-path` or `CLLM_PATH` set)
  5. Local project: `./.cllm/conversations/` (if `.cllm` exists)
  6. Global home: `~/.cllm/conversations/` (fallback)
- ID generation: UUID-based (`conv-<8-char-hex>`) or user-specified
- Features: Atomic writes, token counting, message history preservation
- Key methods: `create()`, `load()`, `save()`, `delete()`, `list_conversations()`

**`src/cllm/config.py`** - Configuration loading (ADR-0003, ADR-0016)

- Loads and merges Cllmfile.yml files with cascading precedence
- Supports named configurations (e.g., `--config summarize`)
- Environment variable interpolation with `${VAR_NAME}` syntax
- File lookup order (default): `~/.cllm/` → `./.cllm/` → `./` (lowest to highest precedence)
- Path override support (ADR-0016): `--cllm-path` CLI flag or `CLLM_PATH` env var
  - Precedence: CLI flag > `CLLM_PATH` > default search order
- CLI arguments always override file-based configuration

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
  config.py        # Configuration file loading (ADR-0003)
  conversation.py  # Conversation management (ADR-0007)
tests/             # Test suite (pytest)
  test_client.py   # LLMClient tests (mock-based)
  test_config.py   # Configuration loading tests
  test_conversation.py  # Conversation management tests
examples/          # Usage examples
  basic_usage.py   # Multi-provider examples
  async_usage.py   # Async patterns
  provider_comparison.py
  configs/         # Example Cllmfile.yml configurations
    Cllmfile.yml   # Default configuration example
    summarize.Cllmfile.yml    # Summarization profile
    creative.Cllmfile.yml     # Creative writing profile
    code-review.Cllmfile.yml  # Code review profile
    README.md      # Configuration guide
docs/decisions/    # Architecture Decision Records (ADRs)
  0001-use-uv-as-package-manager.md
  0002-use-litellm-for-llm-provider-abstraction.md
  0003-cllmfile-configuration-system.md
  0005-structured-output-json-schema.md
  0006-support-remote-json-schema-urls.md
  0007-conversation-threading-and-context-management.md
  0016-configurable-cllm-directory-path.md
  0017-configurable-conversations-path.md
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
- `test_client.py`: 11 tests for LLMClient functionality
- `test_config.py`: 27 tests for configuration loading, merging, and precedence
- `test_conversation.py`: 36 tests for conversation management (CRUD, ID validation, persistence)
- `test_cli.py`: 19 tests for CLI functionality
- All 133 tests should pass

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

### ADR-0003: Cllmfile Configuration System

- **Why:** Reduce repetitive CLI flags, enable shareable configurations, support complex parameter sets
- **File format:** YAML with environment variable interpolation (`${VAR_NAME}`)
- **File lookup order:** `~/.cllm/` → `./.cllm/` → `./` (lowest to highest precedence)
- **Named configs:** Use `--config <name>` to load `<name>.Cllmfile.yml`
- **Precedence:** File configs < CLI arguments (CLI always wins)
- **Key features:**
  - All LiteLLM parameters supported (model, temperature, max_tokens, fallbacks, etc.)
  - `default_system_message` for reusable prompts
  - `--show-config` to debug effective configuration
  - See `examples/configs/` for templates

**Example - Using Named Configurations:**

```bash
# Summarize a document
cat article.md | cllm --config summarize

# Generate creative content
echo "Write a sci-fi story" | cllm --config creative

# Review code changes
git diff | cllm --config code-review

# Override config with CLI args
cllm --config summarize --temperature 0.5 < doc.txt
```

**Example Cllmfile.yml:**

```yaml
# Project-specific defaults
model: "gpt-4"
temperature: 0.7
max_tokens: 1000
timeout: 60
num_retries: 2

# Fallback models
fallbacks:
  - "gpt-3.5-turbo-16k"
  - "claude-3-sonnet-20240229"

# Environment variables
api_key: "${OPENAI_API_KEY}"

# Custom system message
default_system_message: "You are a helpful coding assistant."
```

### ADR-0007: Conversation Threading and Context Management

- **Why:** Enable multi-turn conversations with context preservation for complex workflows like code reviews, iterative debugging, and exploratory conversations
- **Storage precedence:** File-based JSON with local-first approach (aligns with ADR-0003):
  1. `./.cllm/conversations/` (project-specific, if `.cllm` directory exists)
  2. `~/.cllm/conversations/` (global, fallback)
- **ID system:** UUID-based auto-generation (`conv-<8-char-hex>`) or user-specified meaningful names
- **Default behavior:** Stateless (no conversation saved unless `--conversation` flag used)
- **Key features:**
  - Atomic file writes (temp file + rename) to prevent corruption
  - Automatic token counting across providers
  - Message history preservation with role tracking
  - List, view, and delete operations for conversation management

**Example - Multi-turn Conversation:**

```bash
# Start a conversation with custom ID
cllm --conversation bug-investigation "Analyze this error: $(cat error.log)"

# Continue with context automatically loaded
cllm --conversation bug-investigation "What could cause this timeout?"

# Keep building on the conversation
cllm --conversation bug-investigation "How should I fix it?"

# Review the full conversation
cllm --show-conversation bug-investigation
```

**Storage Format:**

```json
{
  "id": "bug-investigation",
  "model": "gpt-4",
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:30:00Z",
  "messages": [
    { "role": "user", "content": "Analyze this error..." },
    { "role": "assistant", "content": "This timeout is likely..." },
    { "role": "user", "content": "What could cause this?" },
    { "role": "assistant", "content": "Several factors..." }
  ],
  "metadata": {
    "total_tokens": 1500
  }
}
```

### ADR-0016: Configurable .cllm Directory Path

- **Why:** Support diverse deployment environments (Docker, CI/CD, testing, custom org structures) that need explicit control over `.cllm` directory location
- **Mechanism:** CLI flag (`--cllm-path`) and environment variable (`CLLM_PATH`)
- **Precedence order:**
  1. `--cllm-path` CLI flag (highest)
  2. `CLLM_PATH` environment variable
  3. Default search order: `./.cllm/` → `~/.cllm/` → `./` (lowest)
- **Behavior:** When custom path specified, ONLY searches that directory (no fallback to defaults)
- **Validation:** Path must exist and be a directory (fails fast with clear error)

**Example - Docker Deployment:**

```dockerfile
# Mount config at custom location
ENV CLLM_PATH=/app/config/.cllm
COPY .cllm/ /app/config/.cllm/
```

**Example - CI/CD (GitHub Actions):**

```yaml
- name: Run CLLM analysis
  env:
    CLLM_PATH: ${{ github.workspace }}/.cllm-ci
  run: cllm --config code-review < diff.txt
```

**Example - Testing (pytest):**

```python
def test_custom_config(tmp_path):
    cllm_dir = tmp_path / ".cllm"
    cllm_dir.mkdir()
    (cllm_dir / "Cllmfile.yml").write_text("model: test-model")

    result = subprocess.run(
        ["cllm", "--cllm-path", str(cllm_dir), "test prompt"],
        capture_output=True
    )
```

**Example - Per-invocation override:**

```bash
# Use default .cllm config normally
cllm "analyze this"

# Override for specific invocation
cllm --cllm-path /tmp/experiment/.cllm "try experimental config"
```

**Example - Init with custom path:**

```bash
# Initialize custom directory
mkdir -p /custom/path
cllm init --cllm-path /custom/path

# Use it
cllm --cllm-path /custom/path "hello world"
```

### ADR-0017: Configurable Conversations Path

- **Why:** Enable independent control over conversation storage and configuration locations for shared conversations, cloud-backed storage, and different retention policies
- **Mechanism:** CLI flag (`--conversations-path`), environment variable (`CLLM_CONVERSATIONS_PATH`), and Cllmfile.yml (`conversations_path`)
- **Precedence order:**
  1. `--conversations-path` CLI flag (highest)
  2. `CLLM_CONVERSATIONS_PATH` environment variable
  3. `conversations_path` in Cllmfile.yml
  4. Custom .cllm path: `<cllm_path>/conversations/` (if `--cllm-path` or `CLLM_PATH` set)
  5. Local project: `./.cllm/conversations/` (if `.cllm` exists)
  6. Global home: `~/.cllm/conversations/` (fallback)
- **Interaction:** Works independently of `--cllm-path` - configuration and conversations can be stored in different locations
- **Use cases:** Shared team conversations, cloud-backed storage, separate retention policies, storage optimization

**Example - Cllmfile.yml configuration:**

```yaml
# .cllm/Cllmfile.yml - Project-specific conversation storage

# Relative path (resolved from current working directory)
conversations_path: ./conversations
conversations_path: ./data/conversations

# Absolute path
conversations_path: /mnt/shared-conversations

# Supports environment variable interpolation
conversations_path: ${HOME}/project-conversations
```

**Example - Shared conversations across projects:**

```bash
# Set up shared conversation storage
export CLLM_CONVERSATIONS_PATH=~/shared-conversations

# All projects share conversation history
cd ~/project1
cllm --conversation code-review "Review these changes"

cd ~/project2
cllm --conversation code-review "Continue reviewing"  # Same conversation!
```

**Example - Cloud-backed storage:**

```bash
# Mount S3 bucket or NFS share
export CLLM_CONVERSATIONS_PATH=/mnt/s3-conversations

# Conversations automatically persisted to cloud
cllm --conversation important-decisions "Document our architecture choice"
```

**Example - Team collaboration:**

```bash
# All team members point to shared network drive
export CLLM_CONVERSATIONS_PATH=/network/team/cllm-conversations

# Team can collaborate on conversations
cllm --conversation team-brainstorm "Let's explore this feature"
```

**Example - Split config and conversations:**

```bash
# Fast local config, durable remote conversations
export CLLM_PATH=~/.cllm                        # Local config
export CLLM_CONVERSATIONS_PATH=/mnt/backup      # Backup-enabled storage

cllm "Process large document"  # Config is fast, conversations are durable
```

**Example - Per-invocation override:**

```bash
# Normal usage stores in default location
cllm --conversation prod "Production conversation"

# Test with temporary location
cllm --conversations-path /tmp/test-conv --conversation test "Test conversation"
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
