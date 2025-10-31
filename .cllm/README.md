# CLLM Project Configurations

This directory contains project-specific CLLM configurations for development workflows. These configurations are automatically available when working in the CLLM project directory.

## Available Configurations

### `Cllmfile.yml` - Default Project Configuration

The default configuration used for general CLLM development work.

**Features:**

- GPT-4 with balanced temperature (0.7)
- Project-specific system message about CLLM architecture
- Fallback to Claude Sonnet and GPT-3.5-turbo-16k

**Usage:**

```bash
echo "How should I implement streaming to file?" | cllm
cat src/cllm/cli.py | cllm "Explain this code"
```

---

### `code-review.Cllmfile.yml` - Code Review

Specialized for reviewing code changes with CLLM-specific best practices.

**Checks:**

- CLLM design principles (bash-first, LiteLLM abstraction)
- Proper use of uv package manager
- Test coverage and mocking patterns
- Security considerations (API keys, yaml.safe_load)

**Usage:**

```bash
git diff | cllm --config code-review
git diff main..feature-branch | cllm --config code-review
```

---

### `docs.Cllmfile.yml` - Documentation Writing

Optimized for writing technical documentation with practical examples.

**Features:**

- Clear, concise language
- Bash piping examples
- Copy-pasteable code snippets
- ADR references

**Usage:**

```bash
echo "Document the config.py module" | cllm --config docs
cat src/cllm/client.py | cllm --config docs "Create API documentation"
```

---

### `test.Cllmfile.yml` - Test Writing

Generates pytest tests following CLLM testing standards.

**Standards:**

- Pytest framework with mocking
- Never calls real LLM APIs
- Uses @patch('cllm.client.completion')
- Organized in test classes
- Comprehensive coverage (happy path + edge cases)

**Usage:**

```bash
cat src/cllm/config.py | cllm --config test "Write tests for this module"
echo "Write tests for environment variable interpolation" | cllm --config test
```

---

### `debug.Cllmfile.yml` - Debugging Help

Analyzes errors and suggests fixes for CLLM-specific issues.

**Helps with:**

- LiteLLM API mocking problems
- Configuration precedence issues
- YAML parsing errors
- Environment variable interpolation
- File lookup path problems

**Usage:**

```bash
cat error.log | cllm --config debug
pytest 2>&1 | cllm --config debug
```

---

### `commit.Cllmfile.yml` - Commit Messages

Generates conventional commit messages from staged changes.

**Format:**

```
<type>(<scope>): <description>

[optional body]
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Usage:**

```bash
git diff --staged | cllm --config commit
git diff --cached src/cllm/config.py | cllm --config commit
```

---

### `refactor.Cllmfile.yml` - Code Refactoring

Suggests refactoring improvements while maintaining behavior.

**Focus:**

- Code clarity and maintainability
- CLLM architecture patterns
- Single responsibility principle
- Type hints and docstrings
- Backwards compatibility

**Usage:**

```bash
cat src/cllm/cli.py | cllm --config refactor "Extract config loading logic"
echo "Simplify the merge_config_with_args function" | cllm --config refactor
```

---

### `adr.Cllmfile.yml` - Architecture Decision Records

Helps draft ADRs following the MADR template.

**Evaluates:**

- Alignment with bash-first design
- Impact on LiteLLM abstraction
- User experience implications
- Testing complexity
- Maintenance burden

**Usage:**

```bash
cllm --config adr "Should we add support for streaming to file?"
echo "Evaluate options for plugin system" | cllm --config adr
```

---

### `explain.Cllmfile.yml` - Code Explanation

Explains code with CLLM-specific context for new developers.

**Approach:**

- High-level purpose first
- Key components and roles
- CLLM patterns (LiteLLM, config, testing)
- ADR references
- Usage examples

**Usage:**

```bash
cat src/cllm/config.py | cllm --config explain
cat tests/test_config.py | cllm --config explain "How do these tests work?"
```

---

### `dynamic-debug.Cllmfile.yml` - LLM-Driven Debugging ⚡ NEW

**Requires:** `--allow-commands` flag (ADR-0013)

Intelligent debugging where the LLM dynamically chooses which commands to execute based on your question.

**The LLM can:**

- Run tests to see failures
- Check git status and recent changes
- Inspect project structure
- Verify dependencies and environment

**Usage:**

```bash
cllm "Why is test_client.py failing?" --config dynamic-debug --allow-commands
cllm "My build is broken" --config dynamic-debug --allow-commands --confirm-commands
```

**How it works:**

1. You ask a question
2. LLM analyzes what information it needs
3. LLM executes relevant commands (e.g., `uv run pytest`, `git diff`)
4. LLM interprets results and provides diagnosis

See [`README-DYNAMIC-COMMANDS.md`](./README-DYNAMIC-COMMANDS.md) for detailed documentation.

---

### `analyze.Cllmfile.yml` - Code Analysis ⚡ NEW

**Requires:** `--allow-commands` flag (ADR-0013)

Comprehensive codebase analysis with advanced tools (ripgrep, find, git).

**Analysis capabilities:**

- Project structure and complexity
- Code metrics and patterns
- Dependency analysis
- TODO/FIXME tracking
- Git history and contributors

**Usage:**

```bash
cllm "What's the codebase complexity?" --config analyze --allow-commands
cllm "Find all API endpoints" --config analyze --allow-commands
cllm "Analyze test coverage" --config analyze --allow-commands
```

---

### `troubleshoot.Cllmfile.yml` - Systematic Troubleshooting ⚡ NEW

**Requires:** `--allow-commands` flag (ADR-0013)

Diagnoses common development issues through systematic command execution.

**Troubleshoots:**

- Broken dependencies
- Environment issues
- Test failures and hangs
- Build problems
- Process conflicts

**Usage:**

```bash
cllm "My dependencies are broken" --config troubleshoot --allow-commands
cllm "Tests are hanging" --config troubleshoot --allow-commands
cllm "Port 8000 already in use" --config troubleshoot --allow-commands
```

---

### `custom-scripts.Cllmfile.yml` - Custom Scripts Template ⚡ NEW

**Requires:** `--allow-commands` flag (ADR-0013)

Template showing how to document custom project scripts so the LLM knows how to use them.

**Demonstrates:**

- Scripts with required parameters
- Scripts with optional flags
- Uncommon tools (jq, fd, rg) with syntax examples
- Safety considerations

**Use this as a starting point for your own project-specific commands.**

See [`README-DYNAMIC-COMMANDS.md`](./README-DYNAMIC-COMMANDS.md) for comprehensive examples and best practices.

---

### `research.Cllmfile.yml` - Codebase Research ⚡ NEW

**Requires:** `--allow-commands` flag (ADR-0013)

Intelligent codebase exploration where the LLM uses search and inspection commands to answer research questions.

**Research capabilities:**

- Find implementations of features
- Understand relationships between components
- Discover design patterns and decisions
- Track down specific code references
- Explore git history and evolution

**The LLM can:**

- Search code with grep (with context)
- Read relevant files
- Find function/class definitions
- Trace imports and dependencies
- Read ADRs and documentation
- Check git history and blame

**Usage:**

```bash
cllm "How does the configuration system work?" --config research --allow-commands
cllm "Find all places where we handle API errors" --config research --allow-commands
cllm "What's the relationship between context and templates?" --config research --allow-commands
cllm "Show me how streaming is implemented" --config research --allow-commands
```

**Example output format:**

> The configuration system works through three main components:
>
> 1. **Config Loading** (`src/cllm/config.py:119`)
>    - `load_config()` finds and merges Cllmfile.yml files
>    - Precedence: ~/.cllm/ → ./.cllm/ → ./
> 2. **Environment Variable Interpolation** (`src/cllm/config.py:33`)
>    - Supports `${VAR_NAME}` syntax
>    - Handled by `_interpolate_env_vars()`
> 3. **CLI Integration** (`src/cllm/cli.py:564`)
>    - Loaded via `load_config(config_name=args.config)`
>    - Merged with CLI args in `merge_config_with_args()`
>
> See ADR-0003 for design rationale.

**Best for:**

- Understanding how features work
- Finding code examples
- Exploring unfamiliar codebases
- Discovering design patterns
- Learning project architecture

---

## Configuration Precedence

When using these configs from the CLLM project directory:

1. **CLI flags** (highest priority)
2. **Named config** via `--config <name>`
3. **Project root** `./Cllmfile.yml`
4. **Project .cllm folder** `./.cllm/Cllmfile.yml` ← **These files**
5. **User home** `~/.cllm/Cllmfile.yml` (lowest priority)

## Tips

### Combining Configs with CLI Overrides

```bash
# Use code-review config but override temperature
git diff | cllm --config code-review --temperature 0.2

# Use test config but request longer responses
cat module.py | cllm --config test --max-tokens 3000
```

### Chaining with Bash

```bash
# Generate commit message and copy to clipboard
git diff --staged | cllm --config commit | pbcopy

# Review, then commit with generated message
git diff | cllm --config code-review
git diff --staged | cllm --config commit | git commit -F -

# Explain code and save to docs
cat src/cllm/client.py | cllm --config explain > docs/client-explanation.md
```

### Viewing Effective Config

```bash
# See what config is being used
cllm --config code-review --show-config

# Check if project config is loaded
cllm --show-config
```

## Creating Custom Configs

To add your own project-specific configuration:

1. Create `<name>.Cllmfile.yml` in this directory
2. Use it with `cllm --config <name>`
3. Consider adding it to this README

**Example:**

```yaml
# profile.Cllmfile.yml
model: "gpt-4"
temperature: 0.5
max_tokens: 1000

default_system_message: |
  Your custom system message for this workflow
```

Usage:

```bash
cllm --config profile "Your prompt here"
```

## Dynamic Command Execution (ADR-0013)

The configurations marked with ⚡ NEW use **LLM-driven dynamic command execution**, where the LLM can intelligently choose and execute shell commands to gather information.

**Key benefits:**

- **Intelligent**: LLM decides what information it needs
- **Efficient**: Only executes relevant commands
- **Safe**: Allowlist/denylist validation, user confirmation options
- **Flexible**: Works with custom scripts and uncommon tools

**Learn more:** See [`README-DYNAMIC-COMMANDS.md`](./README-DYNAMIC-COMMANDS.md) for:

- Detailed usage guide
- How to write effective command descriptions
- Safety best practices
- Examples by use case
- Creating your own configurations

## See Also

- [ADR-0003: Cllmfile Configuration System](../docs/decisions/0003-cllmfile-configuration-system.md)
- [ADR-0013: LLM-Driven Dynamic Command Execution](../docs/decisions/0013-llm-driven-dynamic-command-execution.md)
- [Dynamic Commands README](./README-DYNAMIC-COMMANDS.md) - Comprehensive guide
- [Configuration Examples](../examples/configs/README.md)
- [CLAUDE.md](../CLAUDE.md) - Full project documentation
