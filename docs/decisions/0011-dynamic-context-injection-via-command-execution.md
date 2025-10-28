# Dynamic Context Injection via Command Execution

## Context and Problem Statement

When interacting with LLMs via the CLI, users frequently need to include dynamic context from their system or codebase—such as git status, file contents, test results, or system diagnostics. Currently, users must manually execute commands, copy their output, and paste it into prompts. This workflow is tedious, error-prone, and breaks the flow of bash-centric scripting that CLLM is designed to enable.

For example, a developer debugging a failing test might need to include:
- The test output (`npm test`)
- The git diff (`git diff`)
- The error log (`cat error.log`)
- System information (`uname -a`)

Manually gathering this context before every LLM call is inefficient and makes it difficult to create reusable workflows.

## Decision Drivers

- **Automation**: Eliminate manual copy-paste for repetitive context gathering
- **Bash-centric design**: Align with CLLM's philosophy of leveraging bash primitives
- **Reusability**: Enable shareable workflows via Cllmfile configurations (ADR-0003)
- **Flexibility**: Support both ad-hoc commands (CLI) and predefined workflows (config)
- **Composability**: Work seamlessly with existing bash piping and CLLM features
- **Safety**: Prevent accidental or malicious command execution
- **Performance**: Handle multiple context sources efficiently
- **Error handling**: Gracefully manage command failures without blocking LLM calls

## Considered Options

### Option 1: Inline Command Substitution (Shell-style syntax)

Allow command execution directly in prompts using `$(command)` or similar syntax.

**Example:**
```bash
cllm "Here's the git status: $(git status). What should I commit?"
```

**Pros:**
- Familiar bash syntax
- Simple for ad-hoc use
- No new CLI flags needed

**Cons:**
- Shell already handles this (redundant)
- Hard to control execution timing
- Limited formatting options
- Security risk if prompts come from untrusted sources

### Option 2: Configuration-Based Context Hooks

Define context commands in Cllmfile.yml that execute before every LLM call.

**Example Cllmfile.yml:**
```yaml
model: gpt-4
context_commands:
  - name: "Git Status"
    command: "git status --short"
  - name: "Recent Errors"
    command: "tail -n 20 error.log"
```

**Pros:**
- Reusable across invocations
- Shareable in project configs
- Structured output formatting
- Clear separation of concerns

**Cons:**
- Not flexible for one-off commands
- Requires config file setup
- Commands run even when not needed

### Option 3: CLI Flag for Ad-Hoc Context Injection

Add `--exec` or `--context-exec` flag to run commands before the LLM call.

**Example:**
```bash
cllm "Analyze this" --exec "git status" --exec "git diff"
```

**Pros:**
- Flexible for one-off use
- No config file needed
- Explicit about what's executed

**Cons:**
- Verbose for repeated workflows
- No reusability
- Hard to share across team

### Option 4: Hybrid Approach (Configuration + CLI Flags)

Combine configuration-based context hooks with CLI flags for flexibility.

**Example:**

*Cllmfile.yml (reusable workflows):*
```yaml
model: gpt-4
context_commands:
  - name: "Project Context"
    command: "git status --short"
  - name: "Test Results"
    command: "npm test --silent"
    on_failure: "warn"  # Don't block if tests fail
```

*CLI (ad-hoc additions):*
```bash
# Use config hooks + add one-time context
cllm "Analyze this bug" --exec "cat error.log"

# Disable config hooks for this call
cllm "Quick question" --no-context-exec

# Override with different commands
cllm "Debug" --exec "git diff HEAD~1" --exec "cat stack-trace.txt"
```

**Pros:**
- Best of both worlds: reusability + flexibility
- Consistent with ADR-0003 (Cllmfile precedence)
- Team can share common workflows
- Users can override/extend per invocation

**Cons:**
- More complex implementation
- Need clear precedence rules
- More documentation required

## Decision Outcome

Chosen option: **Option 4: Hybrid Approach (Configuration + CLI Flags)**, because it:

1. **Aligns with existing architecture**: Follows the Cllmfile precedence model (ADR-0003) where configs provide defaults and CLI flags override
2. **Maximizes flexibility**: Teams can define common workflows while individuals can customize per-invocation
3. **Supports bash-centric design**: Commands are explicit and composable with shell features
4. **Enables reusability**: Configurations like `--config debug` can bundle relevant context commands
5. **Maintains safety**: Execution is always explicit (no implicit command evaluation in strings)

### Consequences

- **Good**, because users can create reusable debugging/analysis workflows without repetitive flags
- **Good**, because it maintains CLLM's bash-first philosophy while adding powerful automation
- **Good**, because command output is clearly labeled and structured (easy to parse for LLM)
- **Good**, because it integrates with existing configuration system (ADR-0003) seamlessly
- **Bad**, because it adds complexity to the CLI and config parsing
- **Bad**, because users must understand execution order and precedence rules
- **Bad**, because arbitrary command execution could be a security risk in shared configs

### Confirmation

This decision will be validated through:

1. **Functional tests**: Verify command execution, output injection, and error handling
2. **Integration tests**: Ensure config + CLI flag precedence works correctly
3. **User feedback**: Test with real debugging and code review workflows
4. **Performance benchmarks**: Ensure parallel command execution is efficient
5. **Security review**: Validate command execution safeguards

## Pros and Cons of the Options

### Option 1: Inline Command Substitution

- Good, because it uses familiar bash syntax
- Good, because it requires no new CLI features
- Neutral, because shell already handles command substitution
- Bad, because it's hard to control formatting and timing
- Bad, because it creates security risks with untrusted input
- Bad, because it doesn't support reusable workflows

### Option 2: Configuration-Based Context Hooks

- Good, because it enables reusable workflows
- Good, because output can be structured and labeled
- Good, because it's shareable across teams
- Neutral, because it requires Cllmfile setup
- Bad, because it's not flexible for ad-hoc commands
- Bad, because commands run even when not needed (overhead)

### Option 3: CLI Flag for Ad-Hoc Context Injection

- Good, because it's explicit and flexible
- Good, because no config file is required
- Neutral, because it's verbose for repeated use
- Bad, because it doesn't support reusability
- Bad, because it's hard to share workflows

### Option 4: Hybrid Approach

- Good, because it combines reusability with flexibility
- Good, because it follows existing Cllmfile patterns (ADR-0003)
- Good, because teams can share workflows while allowing customization
- Good, because it supports both quick debugging and structured analysis
- Neutral, because implementation is more complex
- Bad, because users need to learn precedence rules
- Bad, because security considerations require careful documentation

## More Information

### Implementation Details

**1. Cllmfile.yml Schema Extension**

```yaml
# New top-level key: context_commands
context_commands:
  - name: "Git Status"             # Label for LLM context
    command: "git status --short"  # Command to execute
    on_failure: "warn"             # "warn" | "ignore" | "fail" (default: "warn")
    timeout: 5                     # Seconds (default: 10)

  - name: "Test Results"
    command: "npm test --silent"
    on_failure: "ignore"           # Don't include if tests fail
```

**2. CLI Flag Design**

```bash
# Execute single command
cllm "Analyze" --exec "git status"

# Execute multiple commands (processed in order)
cllm "Debug" --exec "git diff" --exec "cat error.log"

# Disable context commands from config
cllm "Quick question" --no-context-exec

# Combine config + CLI (config runs first, then CLI --exec commands)
cllm "Review" --config debug --exec "cat additional.log"
```

**3. Output Format**

Commands inject context as structured blocks in the prompt:

```
--- Context: Git Status ---
M src/cllm/cli.py
M README.md
?? new-feature.py
--- End Context ---

--- Context: Test Results ---
FAIL: test_feature_x
Expected: 42, Got: 43
--- End Context ---

[User's original prompt]
```

**4. Execution Model**

- Commands run **before** the LLM call (not during streaming)
- Commands run **in parallel** where possible (configurable)
- Failures are handled per `on_failure` setting:
  - `warn`: Include error message in context
  - `ignore`: Skip this command's output
  - `fail`: Abort LLM call with error message
- Command output is captured (stdout + stderr)
- Working directory: same as `cllm` invocation

**5. Security Considerations**

- **Explicit execution only**: No implicit command evaluation in prompts
- **Working directory isolation**: Commands run in CWD (no `cd` allowed)
- **User confirmation** (optional): Add `--confirm-context-exec` flag for untrusted configs
- **Audit logging**: Log executed commands when `--debug` is enabled
- **Documentation warnings**: Clearly state risks of running untrusted Cllmfiles

---

## AI-Specific Extensions

### AI Guidance Level

**Flexible**: Core functionality (config parsing, command execution, output injection) should follow this spec precisely. Implementation details (error messages, output formatting tweaks) can be adapted for better UX.

### AI Tool Preferences

- **Preferred AI tools**: Claude Code for implementation
- **Model parameters**: Default settings (no special requirements)
- **Special instructions**:
  - Ensure thread-safe parallel command execution
  - Use `subprocess` with timeout protection
  - Follow existing config precedence patterns from ADR-0003

### Test Expectations

**Unit tests:**
- Parse `context_commands` from Cllmfile.yml correctly
- Handle `--exec` CLI flag and build command list
- Apply precedence rules (config + CLI overrides)
- Format output blocks with proper labels

**Integration tests:**
- Execute commands and capture output
- Handle command failures per `on_failure` setting
- Inject context into prompt correctly
- Verify parallel execution improves performance
- Test timeout protection

**End-to-end tests:**
- Real workflow: `git status` + `git diff` → code review prompt
- Real workflow: `pytest` output → test failure analysis
- Error handling: Non-existent command, timeout, permission denied

**Security tests:**
- Verify no shell injection vulnerabilities
- Confirm commands run in CWD only
- Validate `--confirm-context-exec` blocks untrusted configs

### Dependencies

- **Related ADRs**:
  - ADR-0003 (Cllmfile Configuration System) - Extends config schema
  - ADR-0007 (Conversation Threading) - Context may be stored in conversation history
- **System components**:
  - `src/cllm/config.py` - Parse `context_commands` from Cllmfile
  - `src/cllm/cli.py` - Add `--exec` and `--no-context-exec` flags
  - `src/cllm/context.py` (new) - Command execution and output formatting
- **External dependencies**:
  - Python `subprocess` module (stdlib)
  - Python `asyncio` for parallel execution (stdlib)

### Timeline

- **Implementation deadline**: None (feature proposal)
- **First review**: After initial implementation PR
- **Revision triggers**:
  - Security vulnerabilities discovered
  - Performance issues with parallel execution
  - User feedback indicates confusing precedence rules

### Risk Assessment

#### Technical Risks

- **Command execution failures**:
  - *Mitigation*: Timeout protection, `on_failure` settings, clear error messages
- **Performance overhead**:
  - *Mitigation*: Parallel execution, configurable timeouts, `--no-context-exec` flag
- **Output size explosion**:
  - *Mitigation*: Document best practices (use `--short`, `--quiet` flags), consider max output size limits

#### Business Risks

- **Security concerns**:
  - *Mitigation*: Clear documentation, explicit execution model, optional confirmation flag
- **Complexity for new users**:
  - *Mitigation*: Start with simple examples, provide templates, make CLI flag optional

### Human Review

- **Review required**: Before implementation (design review), after implementation (code review)
- **Reviewers**: Project maintainers, security-conscious users
- **Approval criteria**:
  - Security model is sound (no shell injection)
  - Precedence rules align with ADR-0003
  - Documentation is clear about risks and best practices
  - Tests cover failure modes and edge cases

### Feedback Log

*To be filled after implementation*

- **Implementation date**: TBD
- **Actual outcomes**: TBD
- **Challenges encountered**: TBD
- **Lessons learned**: TBD
- **Suggested improvements**: TBD
