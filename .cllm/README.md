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

## See Also

- [ADR-0003: Cllmfile Configuration System](../docs/decisions/0003-cllmfile-configuration-system.md)
- [Configuration Examples](../examples/configs/README.md)
- [CLAUDE.md](../CLAUDE.md) - Full project documentation
