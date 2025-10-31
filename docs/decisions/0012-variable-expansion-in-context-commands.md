# Variable Expansion in Context Commands with Jinja2 Templates

## Context and Problem Statement

ADR-0011 introduced dynamic context injection via command execution, allowing users to run commands like `git status` or `cat error.log` to inject context into LLM prompts. However, these commands are currently static—defined once in Cllmfile.yml or passed via `--exec` flags. Many real-world workflows require **parameterized context commands** where values change per invocation:

- Analyzing specific files: `cat {{ FILE_PATH }}` where `FILE_PATH` varies
- Reviewing specific git commits: `git show {{ COMMIT_SHA }}`
- Debugging specific test cases: `pytest -k {{ TEST_NAME }} -v`
- Fetching issue details: `gh issue view {{ ISSUE_ID }}`
- Comparing branches: `git diff {{ BASE_BRANCH }}..{{ FEATURE_BRANCH }}`
- Conditional logic: `{% if VERBOSE %}--verbose{% endif %}`
- Transformations: `cat {{ FILE_PATH | upper }}` or `git log -n {{ MAX_COMMITS | default(10) }}`

Currently, users must:

1. Create separate Cllmfile configurations for each parameter combination, OR
2. Manually construct `--exec` commands with hardcoded values each time, OR
3. Use environment variables (which pollute the shell environment)

This limits reusability and makes it difficult to create generic, shareable workflows that adapt to different contexts.

## Decision Drivers

- **Workflow reusability**: Enable generic configurations that work across different files, branches, tickets, etc.
- **CLI ergonomics**: Make it easy to pass parameters without verbose command construction
- **Expressiveness**: Support conditional logic, filters, and transformations beyond simple variable substitution
- **Composability**: Work seamlessly with existing `context_commands` and `--exec` features
- **Security**: Prevent command injection vulnerabilities from untrusted inputs with sandboxed template execution
- **Precedence clarity**: Establish clear rules for variable resolution (CLI > config > env)
- **Documentation**: Variables should be self-documenting in Cllmfile.yml
- **Maintainability**: Use a well-tested, industry-standard template engine rather than custom parsing

## Considered Options

### Option 1: Environment Variables Only (Status Quo Extended)

Leverage existing environment variable interpolation from ADR-0003, requiring users to set shell env vars.

**Example:**

```bash
# Set env vars in shell
export FILE_PATH="src/main.py"
export BRANCH="feature/new-feature"

# Use in commands
cllm "Review this" --exec "cat ${FILE_PATH}" --exec "git diff main..${BRANCH}"
```

**Pros:**

- Already implemented (no new code needed)
- Standard Unix approach
- Works in scripts naturally

**Cons:**

- Pollutes shell environment with temporary variables
- Not user-friendly for interactive use
- No way to document expected variables in Cllmfile.yml
- No validation or defaults for missing variables
- Can't easily override on a per-invocation basis

### Option 2: Dedicated CLI Flags for Variable Passing (Simple String Substitution)

Add `--var KEY=VALUE` or `--define KEY=VALUE` flags to set variables that are expanded in context commands using simple string substitution or basic template syntax.

**Example:**

```bash
# Define variables via CLI
cllm "Review this" \
  --var FILE_PATH=src/main.py \
  --var BRANCH=feature/new-feature \
  --exec "cat {{ FILE_PATH }}" \
  --exec "git diff main..{{ BRANCH }}"
```

**Cllmfile.yml with variable declarations:**

```yaml
# Declare expected variables with defaults
variables:
  FILE_PATH: "README.md" # Default value
  BRANCH: "main" # Default value
  TEST_NAME: null # Required (no default)

context_commands:
  - name: "File Contents"
    command: "cat {{ FILE_PATH }}"
  - name: "Branch Diff"
    command: "git diff main..{{ BRANCH }}"
```

**Pros:**

- Explicit and self-documenting
- Variables scoped to single invocation (no shell pollution)
- Easy to validate and provide defaults in config
- Clear precedence: CLI flags > Cllmfile defaults > environment variables
- Can document required vs optional variables

**Cons:**

- More verbose CLI for multiple variables
- Requires new parsing logic
- Another CLI flag to remember

### Option 3: Positional Arguments with Named Parameters

Use positional arguments or a special syntax to pass parameters.

**Example:**

```bash
# Positional style
cllm "Review this" --exec "cat {1}" --exec "git diff main..{2}" src/main.py feature/new-feature

# Or keyword style
cllm "Review this" --param file=src/main.py --param branch=feature/new-feature
```

**Pros:**

- Concise for simple cases
- Familiar from shell scripting

**Cons:**

- Positional args are fragile (order matters)
- Hard to understand without context
- Doesn't work well with Cllmfile.yml declarations
- Less readable than named variables

### Option 4: Jinja2 Template Engine with Hybrid Variable Sources

Use Jinja2 as the template engine, combining `--var` CLI flags with environment variable fallback and Cllmfile.yml defaults, following established precedence rules from ADR-0003.

**Template Engine Choice: Jinja2**

- Industry-standard Python template engine (used by Ansible, Flask, Django, etc.)
- Sandboxed execution environment for security
- Rich feature set: filters (`| upper`, `| default`), conditionals (`{% if %}`), loops
- Clear syntax: `{{ variable }}` for output, `{% ... %}` for logic
- Excellent error messages with line numbers
- Well-documented and battle-tested

**Variable Resolution Order:**

1. CLI flags (`--var KEY=VALUE`) - highest precedence
2. Environment variables (`$KEY`)
3. Cllmfile.yml defaults (`variables:` section)
4. Error if variable is required and not set

**Example:**

_Cllmfile.yml:_

```yaml
# Document expected variables
variables:
  FILE_PATH: "README.md" # Default value
  BRANCH: "main" # Default value
  TEST_NAME: null # Required (must be provided)
  VERBOSE: false # Boolean flag
  MAX_LINES: 50 # Numeric value

context_commands:
  - name: "File Contents"
    command: "cat {{ FILE_PATH }} | head -n {{ MAX_LINES }}"

  - name: "Git Diff"
    command: "git diff main..{{ BRANCH }} {% if VERBOSE %}--stat{% endif %}"

  - name: "Test Output"
    command: "pytest -k {{ TEST_NAME }} {% if VERBOSE %}-vv{% else %}-v{% endif %}"
```

_CLI Usage:_

```bash
# Override with CLI flags
cllm "Review" --var FILE_PATH=src/app.py --var TEST_NAME=test_login

# Use config defaults
cllm "Review"  # Uses FILE_PATH=README.md, BRANCH from env/default

# Mix CLI and env vars
export BRANCH=feature/auth
cllm "Review" --var FILE_PATH=src/auth.py  # Uses CLI file, env branch
```

**Pros:**

- Maximum flexibility: CLI for one-offs, config for shared workflows, env for scripting
- Clear precedence rules consistent with ADR-0003
- Self-documenting (variables declared in Cllmfile.yml)
- Supports validation and required variables
- No shell environment pollution for CLI flags
- Backward compatible (env vars still work)

**Cons:**

- Most complex implementation
- Users need to understand three-layer precedence
- More documentation required

## Decision Outcome

Chosen option: **Option 4: Jinja2 Template Engine with Hybrid Variable Sources**, because it:

1. **Maximizes flexibility**: Supports quick one-off invocations (CLI), reusable workflows (config), and scripting (env vars)
2. **Aligns with existing patterns**: Follows the same precedence model as ADR-0003 (CLI > config > env)
3. **Improves documentation**: Variables declared in Cllmfile.yml serve as built-in documentation
4. **Enables validation**: Can enforce required variables and provide helpful error messages with Jinja2's built-in undefined checking
5. **Provides expressiveness**: Jinja2 filters, conditionals, and logic enable sophisticated command construction
6. **Reduces shell pollution**: CLI flags don't require exporting variables to shell environment
7. **Ensures security**: Jinja2's sandboxed environment prevents code execution vulnerabilities
8. **Industry standard**: Well-tested, documented, and familiar to many developers

### Consequences

- **Good**, because users can create truly reusable workflow templates (e.g., `--config review-file --var FILE_PATH=...`)
- **Good**, because variables are self-documenting in Cllmfile.yml (team members can see what's expected)
- **Good**, because CLI flags provide ergonomic override mechanism without shell pollution
- **Good**, because Jinja2's filters and conditionals enable powerful command construction without shell scripting
- **Good**, because Jinja2's sandboxed environment provides strong security guarantees
- **Good**, because Jinja2's error messages pinpoint issues clearly with line numbers and context
- **Good**, because validation prevents cryptic errors from missing variables
- **Good**, because it works seamlessly with existing `--exec` and `context_commands` features
- **Good**, because Jinja2 is widely known (Ansible, Flask, etc.), reducing learning curve
- **Bad**, because three-layer precedence adds conceptual complexity
- **Bad**, because adds Jinja2 as an external dependency
- **Bad**, because users need to learn Jinja2 syntax (though it's intuitive for basic use)

### Confirmation

This decision will be validated through:

1. **Unit tests**: Variable resolution with all three sources (CLI, env, config)
2. **Precedence tests**: Verify CLI > config > env order
3. **Validation tests**: Required variables, defaults, missing variable errors
4. **Integration tests**: Real workflows with parameterized context commands
5. **Security tests**: Command injection prevention with untrusted variable values
6. **User testing**: Feedback on ergonomics and documentation clarity

## Pros and Cons of the Options

### Option 1: Environment Variables Only

- Good, because it uses standard Unix patterns
- Good, because no implementation needed (already supported)
- Good, because works naturally in shell scripts
- Neutral, because familiar to Unix users but not to others
- Bad, because pollutes shell environment with temporary variables
- Bad, because not self-documenting in configs
- Bad, because no validation or default mechanism
- Bad, because awkward for interactive CLI use

### Option 2: Dedicated CLI Flags for Variable Passing

- Good, because explicit and clear
- Good, because variables scoped to single invocation
- Good, because supports validation and defaults in config
- Good, because self-documenting via Cllmfile.yml declarations
- Neutral, because requires learning new `--var` syntax
- Bad, because verbose for many variables
- Bad, because doesn't leverage existing environment variables

### Option 3: Positional Arguments with Named Parameters

- Good, because concise for simple cases
- Good, because familiar from shell scripting (`{1}`, `{2}`)
- Neutral, because works for ad-hoc use but not for configs
- Bad, because positional arguments are order-dependent and fragile
- Bad, because not self-documenting
- Bad, because doesn't integrate well with Cllmfile.yml
- Bad, because harder to read and maintain

### Option 4: Jinja2 Template Engine with Hybrid Variable Sources

- Good, because maximizes flexibility for all use cases
- Good, because aligns with existing ADR-0003 precedence model
- Good, because self-documenting via variable declarations
- Good, because Jinja2 provides rich templating features (filters, conditionals, loops)
- Good, because sandboxed execution prevents security vulnerabilities
- Good, because industry-standard tool with excellent documentation
- Good, because supports validation and helpful error messages
- Good, because no shell pollution for CLI-provided variables
- Good, because Jinja2 is familiar to many developers (Ansible, Flask, Django)
- Neutral, because adds external dependency (but Jinja2 is lightweight and stable)
- Bad, because three-layer precedence requires clear documentation
- Bad, because requires learning Jinja2 syntax for advanced features

## More Information

### Implementation Details

**1. Cllmfile.yml Schema Extension**

```yaml
# New top-level section: variables
variables:
  # Simple default value
  FILE_PATH: "README.md"

  # Environment variable (resolved at runtime)
  BRANCH: "main"

  # Required variable (no default)
  ISSUE_ID: null

  # Numeric/boolean values
  MAX_LINES: 100
  VERBOSE: true

# Variables used in Jinja2 templates within context commands
context_commands:
  - name: "File Contents"
    command: "cat {{ FILE_PATH }} | head -n {{ MAX_LINES }}"

  - name: "File Contents (Conditional)"
    command: "cat {{ FILE_PATH }} {% if VERBOSE %}| cat -n{% endif %}"

  - name: "Issue Details"
    command: "gh issue view {{ ISSUE_ID }}"

  - name: "Git Log (with filter)"
    command: "git log -n {{ MAX_LINES | default(10) }} {{ BRANCH }}"
```

**2. CLI Flag Design**

```bash
# Single variable
cllm "Prompt" --var FILE_PATH=src/main.py

# Multiple variables
cllm "Prompt" --var FILE_PATH=src/main.py --var BRANCH=feature/auth --var ISSUE_ID=123

# Short form (optional)
cllm "Prompt" -v FILE_PATH=src/main.py -v BRANCH=main

# Combined with --exec (Jinja2 templates expand in ad-hoc commands too)
cllm "Analyze" --var FILE=test.py --exec "cat {{ FILE }}" --exec "pylint {{ FILE }}"

# Using Jinja2 filters and conditionals
cllm "Review" --var FILE=src/main.py --var VERBOSE=true \
  --exec "cat {{ FILE }} {% if VERBOSE %}| cat -n{% endif %}"

# Show resolved variables (debugging)
cllm --show-config --var FILE=test.py  # Shows resolved variable values
```

**3. Variable Resolution and Context Building**

```python
from typing import Any, Dict
import os

def build_template_context(cli_vars: Dict[str, Any],
                          config_vars: Dict[str, Any],
                          env_vars: Dict[str, str]) -> Dict[str, Any]:
    """
    Build Jinja2 context dict with precedence: CLI > Config > Environment

    Args:
        cli_vars: Variables from --var CLI flags
        config_vars: Variables from Cllmfile.yml (may contain None for required vars)
        env_vars: Environment variables

    Returns:
        Dict of resolved variables for Jinja2 template context

    Raises:
        ValueError: If required variable (config value is None) is not provided
    """
    context = {}

    # Start with config defaults
    for var_name, config_value in config_vars.items():
        # Required variable (None) - must come from CLI or env
        if config_value is None:
            if var_name in cli_vars:
                context[var_name] = cli_vars[var_name]
            elif var_name in env_vars:
                context[var_name] = env_vars[var_name]
            else:
                raise ValueError(
                    f"Required variable '{var_name}' not provided via --var flag or environment"
                )
        else:
            context[var_name] = config_value

    # Override with environment variables
    for var_name, env_value in env_vars.items():
        if var_name in context:
            context[var_name] = env_value

    # Override with CLI variables (highest precedence)
    context.update(cli_vars)

    return context
```

**4. Jinja2 Template Rendering with Sandboxing**

```python
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment
import shlex
from typing import Dict, Any

def create_jinja_env() -> SandboxedEnvironment:
    """
    Create a sandboxed Jinja2 environment for secure template rendering.

    - SandboxedEnvironment prevents dangerous operations (file access, code execution)
    - StrictUndefined raises errors for undefined variables (fail fast)
    - Custom filters for shell operations
    """
    env = SandboxedEnvironment(
        undefined=StrictUndefined,
        autoescape=False,  # We're generating shell commands, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filter for shell escaping
    env.filters['shellquote'] = shlex.quote

    return env

def render_command_template(command_template: str, context: Dict[str, Any]) -> str:
    """
    Render a Jinja2 template with variable context.

    Args:
        command_template: Jinja2 template string (e.g., "cat {{ FILE }} | head")
        context: Dict of variables (e.g., {"FILE": "test.py"})

    Returns:
        Rendered command string with variables expanded

    Raises:
        TemplateSyntaxError: Invalid Jinja2 syntax
        UndefinedError: Variable used in template but not in context
    """
    env = create_jinja_env()

    try:
        template = env.from_string(command_template)
        # Render with automatic shell quoting for safety
        rendered = template.render(context)
        return rendered.strip()
    except TemplateSyntaxError as e:
        raise ValueError(f"Template syntax error in command: {e.message} (line {e.lineno})")
    except UndefinedError as e:
        raise ValueError(f"Undefined variable in command template: {e}")

# Example usage:
# context = {"FILE": "test.py", "VERBOSE": True, "MAX_LINES": 50}
# command = render_command_template("cat {{ FILE }} {% if VERBOSE %}-n{% endif %}", context)
# Result: "cat test.py -n"
```

**5. Error Handling and Messages**

```bash
# Missing required variable
$ cllm "Analyze" --config review  # Config requires FILE_PATH
Error: Required variable 'FILE_PATH' not provided via --var flag or environment

  Declare it in your command:
    cllm "Analyze" --config review --var FILE_PATH=src/main.py

  Or set it as environment variable:
    export FILE_PATH=src/main.py

# Undefined variable in Jinja2 template
$ cllm "Test" --exec "cat {{ UNKNOWN_VAR }}"
Error: Undefined variable in command template: 'UNKNOWN_VAR' is undefined

  Available variables:
    - FILE_PATH (from Cllmfile.yml)
    - BRANCH (from CLI --var)
    - MAX_LINES (from environment)

  Add missing variable:
    cllm "Test" --var UNKNOWN_VAR=value --exec "cat {{ UNKNOWN_VAR }}"

# Template syntax error
$ cllm "Test" --exec "cat {{ FILE }}"  # Missing closing braces
Error: Template syntax error in command: unexpected end of template (line 1)

  Check your template syntax:
    - Variables: {{ VAR_NAME }}
    - Conditionals: {% if CONDITION %}...{% endif %}
    - Filters: {{ VAR | filter }}

  See Jinja2 docs: https://jinja.palletsprojects.com/
```

**6. Security Considerations with Jinja2**

- **Sandboxed execution**: `SandboxedEnvironment` prevents dangerous operations:
  - No file system access from templates
  - No module imports or arbitrary code execution
  - No access to private attributes (underscore-prefixed)
  - Restricted to safe operations only
- **Strict undefined checking**: `StrictUndefined` causes immediate errors for undefined variables (fail-fast)
- **Custom shell escaping filter**: `shellquote` filter available for explicit escaping when needed
- **No eval or exec**: Jinja2 never executes Python code from template strings
- **Audit logging**: When `--debug` is enabled, log resolved variable values (except sensitive ones)
- **Sensitive variables**: Support marking variables as sensitive (e.g., `API_KEY: !sensitive`) to redact from logs

**Example - Security:**

```bash
# Safe: Jinja2 sandboxing prevents code execution
cllm --var FILE="test.txt; rm -rf /" --exec "cat {{ FILE }}"
# Renders to: cat test.txt; rm -rf /
# (Note: This is passed to shell, so user should use shellquote filter)

# Better: Use shellquote filter for untrusted input
cllm --var FILE="test.txt; rm -rf /" --exec "cat {{ FILE | shellquote }}"
# Renders to: cat 'test.txt; rm -rf /' (safely escaped)

# Sandboxed environment blocks dangerous operations
cllm --var FILE="test.py" --exec "{{ FILE.__class__.__bases__ }}"
# Error: Access to attribute '__class__' is unsafe (SecurityError)

# No file access from templates
cllm --exec "{% include '/etc/passwd' %}"
# Error: Template sandbox restricts file operations
```

**Security Best Practices:**

1. **Use `shellquote` filter for untrusted input**: `{{ USER_INPUT | shellquote }}`
2. **Never disable sandboxing**: Always use `SandboxedEnvironment`, not plain `Environment`
3. **Validate variable names**: CLI parser should restrict to `[A-Za-z_][A-Za-z0-9_]*`
4. **Audit shared configs**: Review Cllmfile.yml templates before running untrusted configs
5. **Enable debug logging for security audits**: `--debug` shows what commands actually execute

---

## AI-Specific Extensions

### AI Guidance Level

**Flexible**: Core functionality (variable resolution precedence, shell escaping, error messages) should follow this spec precisely. Implementation details (error message formatting, debugging output) can be adapted for better UX based on testing and user feedback.

### AI Tool Preferences

- **Preferred AI tools**: Claude Code for implementation
- **Model parameters**: Default settings (no special requirements)
- **Special instructions**:
  - Use Jinja2's `SandboxedEnvironment` exclusively (never plain `Environment`)
  - Configure `StrictUndefined` to catch undefined variable errors early
  - Add custom `shellquote` filter using `shlex.quote()` for shell safety
  - Follow existing config loading patterns from `src/cllm/config.py`
  - Validate variable names before allowing declaration (`[A-Za-z_][A-Za-z0-9_]*`)
  - Provide helpful error messages with actionable suggestions and Jinja2 docs links
  - Handle Jinja2 exceptions gracefully (TemplateSyntaxError, UndefinedError, SecurityError)

### Test Expectations

**Unit tests:**

- Parse `variables:` section from Cllmfile.yml correctly
- Resolve variables with correct precedence (CLI > config > env)
- Handle required variables (null defaults) with proper errors
- Validate variable name patterns (alphanumeric + underscore only)
- Render Jinja2 templates correctly with `{{ VAR }}` syntax
- Support Jinja2 conditionals (`{% if %}...{% endif %}`)
- Support Jinja2 filters (`{{ VAR | default(value) }}`, `{{ VAR | shellquote }}`)
- Catch undefined variables with StrictUndefined
- Raise TemplateSyntaxError for invalid Jinja2 syntax

**Integration tests:**

- Load config, pass CLI vars, render templates in context commands
- Override config defaults with CLI flags
- Fall back to environment variables correctly
- Handle missing required variables with helpful errors
- `--show-config` displays resolved variable values
- Complex templates with multiple conditionals and filters

**Security tests:**

- Sandboxed environment blocks file access attempts
- Sandboxed environment blocks attribute access (`__class__`, etc.)
- Sandboxed environment blocks module imports
- `shellquote` filter properly escapes shell metacharacters
- Invalid variable names are rejected at CLI parsing stage
- No code evaluation occurs (SecurityError raised for unsafe operations)
- Sensitive variables can be redacted from logs

**End-to-end tests:**

- Real workflow: `--var FILE_PATH=src/main.py` → `cat {{ FILE_PATH }}` → correct file content
- Real workflow: Git diff with parameterized branches and conditionals
- Real workflow: Using filters for transformations (`{{ BRANCH | upper }}`)
- Error handling: Missing required variable, undefined variable in template, syntax errors

### Dependencies

- **Related ADRs**:
  - ADR-0003 (Cllmfile Configuration System) - Extends variable system
  - ADR-0011 (Dynamic Context Injection) - Extends `context_commands` and `--exec`
- **System components**:
  - `src/cllm/config.py` - Parse `variables:` section from Cllmfile
  - `src/cllm/cli.py` - Add `--var` flag and resolution logic
  - `src/cllm/context.py` - Jinja2 template rendering and variable expansion in command execution
- **External dependencies**:
  - **Jinja2** (`jinja2` package) - Template engine for variable expansion, conditionals, and filters
    - Version: `^3.1.0` (latest stable)
    - License: BSD-3-Clause
    - Size: ~200KB (lightweight)
    - Well-maintained by Pallets project
  - Python `shlex` module (stdlib) - Safe shell escaping (used in custom filter)
  - Python `os` module (stdlib) - Environment variable access

### Timeline

- **Implementation deadline**: None (feature proposal)
- **First review**: After initial implementation PR
- **Revision triggers**:
  - Security vulnerabilities discovered in variable expansion
  - User feedback indicates confusing precedence rules
  - Need for more complex variable features (arrays, nested substitution)

### Risk Assessment

#### Technical Risks

- **Command injection vulnerabilities**:
  - _Mitigation_: Use Jinja2's `SandboxedEnvironment`, provide `shellquote` filter, validate variable names, encourage best practices in docs
- **Variable resolution bugs**:
  - _Mitigation_: Comprehensive tests for all precedence combinations, leverage Jinja2's `StrictUndefined` for early error detection
- **Performance overhead**:
  - _Mitigation_: Cache Jinja2 environment instance, cache resolved variable context per invocation, Jinja2 is highly optimized
- **Template complexity leading to errors**:
  - _Mitigation_: Clear error messages from Jinja2, provide examples in docs, start with simple templates
- **Dependency on external package**:
  - _Mitigation_: Jinja2 is stable, widely-used, and well-maintained; version pin in requirements

#### Business Risks

- **User confusion about precedence**:
  - _Mitigation_: Clear documentation, `--show-config` debugging output, helpful error messages
- **User confusion about Jinja2 syntax**:
  - _Mitigation_: Provide clear examples, link to Jinja2 docs, start with simple variable substitution examples
- **Breaking changes to existing workflows**:
  - _Mitigation_: This is a new feature, no existing workflows use templating yet
- **Feature complexity creep**:
  - _Mitigation_: Start with core Jinja2 features (variables, conditionals, basic filters), document advanced features separately
- **Adoption resistance due to new syntax**:
  - _Mitigation_: Jinja2 is familiar to many developers, provide migration examples, show benefits in docs

### Human Review

- **Review required**: Before implementation (design review), after implementation (code + security review)
- **Reviewers**: Project maintainers, security-focused contributors, Jinja2 experts
- **Approval criteria**:
  - Variable resolution precedence is correct and well-tested
  - Jinja2 `SandboxedEnvironment` is used exclusively (never plain `Environment`)
  - `shellquote` filter is properly implemented and encouraged in docs
  - Security testing covers sandbox restrictions thoroughly
  - Error messages are clear and actionable (with Jinja2 docs links)
  - Documentation explains all three variable sources with examples
  - Documentation includes Jinja2 template examples (simple to advanced)
  - Tests cover all precedence combinations, template features, and edge cases
  - Jinja2 dependency is properly versioned in `pyproject.toml`

### Feedback Log

- **Implementation date**: 2025-10-28
- **Actual outcomes**:
  - Implemented sandboxed templating utilities with `StrictUndefined`, cached environment reuse, and a `shellquote` filter (`src/cllm/templates.py:19`).
  - Wired CLI variable parsing, precedence handling, and `--show-config` variable introspection, then passed the resolved context into context injection (`src/cllm/cli.py:249` and `src/cllm/cli.py:627`).
  - Added context-aware rendering prior to execution plus error surfacing that lists available variables (`src/cllm/context.py:259`).
  - Extended the test suite with precedence, validation, and rendering assertions (`tests/test_templates.py:18`, `tests/test_templates.py:50`, `tests/test_context.py:268`).
  - Documented and smoke-tested a templated workflow example (`examples/bash/templated-context.sh:1`, `examples/bash/README.md:49`, `tests/examples/test_bash_examples.py:29`).
- **Challenges encountered**:
  - Full end-to-end coverage of CLI flag parsing with configuration overlays is still pending; current tests exercise lower layers only.
  - Security-focused regression tests (e.g., asserting sandbox denies attribute access) were deferred due to time constraints.
- **Lessons learned**:
  - Centralising template rendering in a dedicated module simplifies sandbox enforcement and keeps CLI logic slimmer.
  - Reusing a single `SandboxedEnvironment` instance avoids needless startup overhead without sacrificing isolation.
- **Suggested improvements**:
  - Add CLI integration tests that load a temporary Cllmfile and verify `--var` precedence alongside environment fallbacks.
  - Introduce explicit negative tests that assert sandbox behaviour for dangerous template expressions (attribute access, includes).
- **Confirmation Status**:
  - ✅ Unit tests cover core template parsing, precedence, and rendering paths.
  - ✅ Precedence ordering (CLI > config > env) validated via dedicated test cases.
  - ✅ Validation errors for missing required variables and undefined template names are exercised.
  - ⚠️ Integration testing through the public CLI/config interface is limited; add `CliRunner` coverage.
  - ⚠️ Security testing lacks direct assertions around sandbox escapes; add targeted regression tests.
  - ❌ User testing feedback not yet collected.
