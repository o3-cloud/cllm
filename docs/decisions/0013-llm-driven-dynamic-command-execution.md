# LLM-Driven Dynamic Command Execution

## Context and Problem Statement

Users frequently ask CLLM questions that require dynamic information from their system or codebase, but the LLM cannot determine what information is needed until it processes the user's prompt. While ADR-0011 (Dynamic Context Injection) allows predefined commands to run automatically, this approach has limitations:

- Commands run regardless of whether they're needed for the prompt
- Users must anticipate what context will be relevant
- The LLM cannot iteratively gather information based on intermediate findings
- Complex workflows require multiple manual invocations

For example, a user might ask: "Why is my build failing?" The LLM needs to:
1. Check the build output (`npm run build` or `make`)
2. If tests are failing, examine test results (`npm test`)
3. If there are type errors, inspect the specific files mentioned
4. If dependencies are missing, check `package.json`

Currently, users must either:
- Pre-configure all possible context commands (wasteful, slow)
- Manually run commands based on LLM suggestions (tedious, breaks flow)
- Use multiple CLLM invocations in a loop (inefficient, loses context)

We need a mechanism for the LLM to **dynamically choose and execute commands** during its reasoning process, creating an agentic workflow where the LLM gathers information as needed.

## Decision Drivers

- **Intelligence**: LLM should decide which commands are relevant to the user's prompt
- **Efficiency**: Only execute commands that are actually needed
- **Iterative reasoning**: LLM should be able to inspect command output and decide next steps
- **Provider compatibility**: Must work across LiteLLM's 100+ providers (not all support tool calling)
- **Bash-centric design**: Commands should be bash commands (aligned with CLLM's philosophy)
- **Safety**: Prevent arbitrary command execution without user control
- **Transparency**: Users should see what commands are being executed
- **Composability**: Should integrate with existing features (ADR-0011, ADR-0003, ADR-0007)
- **User control**: Users should be able to approve/deny commands or configure allowlists

## Considered Options

### Option 1: LiteLLM Tool/Function Calling

Use LiteLLM's native tool calling support to provide the LLM with command execution capabilities.

**Example:**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash_command",
            "description": "Execute a bash command and return its output",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"},
                    "reason": {"type": "string", "description": "Why this command is needed"}
                },
                "required": ["command", "reason"]
            }
        }
    }
]

# LLM decides to call: execute_bash_command(command="npm test", reason="Check test failures")
# System executes command, returns output
# LLM continues with the information
```

**Pros:**
- Native LLM capability (GPT-4, Claude, Gemini support tool calling)
- Well-defined interface and error handling
- LLM can chain multiple tool calls
- Industry-standard pattern

**Cons:**
- Not all providers support tool calling equally
- Requires structured outputs (may not work with all models)
- More complex implementation

### Option 2: Prompt-Based Command Requests

Define a special syntax in prompts where the LLM can request command execution.

**Example:**
```markdown
LLM Output:
To answer this question, I need to check the build output.

[EXECUTE: npm run build]

(System runs command, injects output)

Based on the build output showing "Module not found: react-router", ...
```

**Pros:**
- Works with any LLM (no tool calling required)
- Simple to implement
- Easy to debug (visible in conversation)

**Cons:**
- Fragile parsing (LLM might not follow format)
- Hard to distinguish commands from markdown code blocks
- No structured metadata (timeouts, error handling preferences)
- Less reliable than native tool calling

### Option 3: Structured Planning Phase

LLM first outputs a JSON plan of commands to execute, then all commands run, then LLM processes results.

**Example:**
```json
{
  "plan": [
    {"command": "git status", "reason": "Check current state"},
    {"command": "npm test", "reason": "Verify test failures"}
  ]
}
```

**Pros:**
- Clear separation of planning and execution
- All commands run in parallel (fast)
- Easy to review/approve before execution

**Cons:**
- No iterative refinement (LLM can't adjust based on results)
- Requires LLM to predict all needed information upfront
- Less flexible than agentic loop

### Option 4: Hybrid Approach (Tool Calling + Fallback)

Use tool calling when available, fall back to prompt-based requests for providers without support.

**Example:**
```bash
# With tool-calling capable model (GPT-4, Claude, Gemini)
cllm "Why is my build failing?" --allow-commands

# With non-tool-calling model (older models)
cllm "Why is my build failing?" --allow-commands --command-syntax prompt
```

**Pros:**
- Best experience on capable models
- Degrades gracefully for simpler models
- Maximum provider compatibility

**Cons:**
- Two codepaths to maintain
- Inconsistent behavior across providers
- More complex testing

## Decision Outcome

Chosen option: **Option 1: LiteLLM Tool/Function Calling**, because it:

1. **Leverages native LLM capabilities**: Tool calling is a standard feature of modern LLMs
2. **Provides structured interface**: Clear parameters, error handling, and metadata
3. **Enables agentic workflows**: LLM can iteratively execute commands and refine its approach
4. **Aligns with industry patterns**: Similar to OpenAI Assistants, Anthropic tool use, etc.
5. **Maintains safety**: Explicit tool definitions with parameter validation
6. **Supports LiteLLM's abstraction**: Works across providers with tool calling support

For providers without tool calling support, we will display a clear error message suggesting the user switch to a compatible model.

### Consequences

- **Good**, because LLM can intelligently choose which commands are relevant to the user's query
- **Good**, because it eliminates the need to pre-configure all possible context commands
- **Good**, because users get answers faster (LLM gathers information automatically)
- **Good**, because it enables complex multi-step debugging and analysis workflows
- **Good**, because tool calling APIs provide structured error handling and timeouts
- **Good**, because command descriptions help the LLM make more accurate command selections
- **Good**, because configurations with descriptions are self-documenting and easier to audit
- **Bad**, because not all LiteLLM providers support tool calling (limits compatibility)
- **Bad**, because it requires user opt-in (safety mechanism) which adds friction
- **Bad**, because command execution can be slower than pre-configured context injection
- **Bad**, because it increases token usage (tool definitions + agentic loop iterations)
- **Bad**, because users must trust the LLM to execute safe commands
- **Bad**, because defining commands with descriptions requires more initial configuration effort

### Confirmation

This decision will be validated through:

1. **Functional tests**: Verify tool calling integration, command execution, output injection
2. **Multi-provider tests**: Ensure compatibility with OpenAI, Anthropic, Google, etc.
3. **Safety tests**: Validate allowlist/denylist filtering and user confirmation flows
4. **Performance benchmarks**: Compare speed vs. pre-configured context injection (ADR-0011)
5. **User workflows**: Test with real debugging scenarios (build failures, test errors, git conflicts)
6. **Token usage analysis**: Monitor cost implications of agentic loops
7. **Command selection accuracy**: Verify LLM chooses correct commands when descriptions are provided vs. simple allowlist

## Pros and Cons of the Options

### Option 1: LiteLLM Tool/Function Calling

- Good, because it uses native LLM capabilities (reliable, well-tested)
- Good, because it supports iterative refinement (LLM can chain commands)
- Good, because tool definitions provide clear structure and validation
- Good, because it's consistent with industry-standard patterns
- Neutral, because it requires user opt-in for safety (adds friction but increases trust)
- Bad, because not all providers support tool calling equally
- Bad, because it increases implementation complexity
- Bad, because it may increase token usage compared to simpler approaches

### Option 2: Prompt-Based Command Requests

- Good, because it works with any LLM (no tool calling required)
- Good, because it's simple to implement
- Neutral, because command requests are visible in conversation
- Bad, because parsing is fragile (LLM might not follow syntax)
- Bad, because there's no structured metadata (timeouts, error preferences)
- Bad, because it's harder to validate and sanitize commands

### Option 3: Structured Planning Phase

- Good, because plans are easy to review before execution
- Good, because all commands can run in parallel (fast)
- Good, because it's deterministic (no agentic loop variability)
- Neutral, because it requires LLM to predict all needed information upfront
- Bad, because LLM cannot adjust based on intermediate results
- Bad, because it's less flexible than iterative approaches

### Option 4: Hybrid Approach

- Good, because it maximizes provider compatibility
- Good, because it provides best experience on capable models
- Neutral, because behavior differs across providers
- Bad, because it requires maintaining two codepaths
- Bad, because testing is more complex
- Bad, because user experience is inconsistent

## More Information

### Implementation Details

**1. CLI Flag Design**

```bash
# Enable dynamic command execution
cllm "Why is my build failing?" --allow-commands

# Restrict to specific commands (allowlist)
cllm "Debug this" --allow-commands --command-allow "git*,npm*,pytest*"

# Deny specific commands (denylist)
cllm "Analyze" --allow-commands --command-deny "rm*,mv*,dd*"

# Require confirmation for each command
cllm "Fix this" --allow-commands --confirm-commands

# Combine with conversation threading (ADR-0007)
cllm "Debug this issue" --conversation debug-session --allow-commands
```

**2. Configuration File Support (Cllmfile.yml)**

```yaml
# Enable dynamic commands in this config
allow_dynamic_commands: true

# Define available tools (commands LLM can use)
dynamic_commands:
  # Option 1: Structured command definitions with descriptions (recommended)
  # This provides context to help the LLM choose the right command
  available_commands:
    # Standard commands
    - command: "git status"
      description: "Show the working tree status - which files are modified, staged, or untracked"

    - command: "git diff"
      description: "Show changes between commits, commit and working tree, etc."

    - command: "git log --oneline -10"
      description: "Show the last 10 commit messages in compact format"

    - command: "npm test"
      description: "Run the project's test suite and show test results"

    - command: "npm run build"
      description: "Build the project and show any compilation errors"

    - command: "cat package.json"
      description: "Display the package.json file to check dependencies and scripts"

    - command: "pytest -v"
      description: "Run Python tests with verbose output"

    - command: "ls -la"
      description: "List all files in the current directory with details"

    # Custom bash scripts with parameters
    - command: "./scripts/check-deps.sh"
      description: "Check for outdated dependencies and security vulnerabilities. Usage: ./scripts/check-deps.sh [--fix] to auto-update"

    - command: "./scripts/analyze-logs.sh <log_file>"
      description: "Analyze log files for errors and patterns. Requires log file path as parameter. Example: ./scripts/analyze-logs.sh logs/app.log"

    # Uncommon commands with specific usage
    - command: "jq '.dependencies' package.json"
      description: "Extract dependencies from package.json using jq (JSON processor). Change '.dependencies' to '.devDependencies' for dev deps"

    - command: "fd -e py -x wc -l"
      description: "Count lines in all Python files using fd (fast find alternative). Use 'fd -e js' for JavaScript files"

    - command: "rg 'TODO|FIXME' --json"
      description: "Search for TODO/FIXME comments using ripgrep with JSON output for structured parsing"

  # Option 2: Simple allowlist with wildcard patterns (less guidance for LLM)
  allow:
    - "git*"           # All git commands
    - "npm test"       # Exact match
    - "pytest*"        # Pattern match
    - "cat *.py"       # File reading
    - "ls*"            # Directory listing

  # Denylist dangerous commands (always checked regardless of above options)
  deny:
    - "rm *"
    - "sudo *"
    - "dd *"
    - "mv *"
    - "> *"            # Prevent redirects that overwrite files

  # Require confirmation
  require_confirmation: false  # true = prompt before each command

  # Timeout for each command
  timeout: 30  # seconds

  # Max number of command executions per LLM call
  max_commands: 10

  # Working directory restriction
  working_directory: "."  # Restrict to current directory and subdirectories
```

**3. Tool Definition for LLM**

The tool definition is dynamically generated based on the configuration. When `available_commands` with descriptions is provided, those descriptions are included to help the LLM choose the right command.

```python
def generate_command_tool(config: dict) -> dict:
    """Generate the tool definition dynamically based on config."""

    # Build description with available commands if defined
    base_description = "Execute a bash command to gather information needed to answer the user's question.\n\n"

    available_commands = config.get("dynamic_commands", {}).get("available_commands", [])
    if available_commands:
        base_description += "Available commands:\n"
        for cmd_def in available_commands:
            cmd = cmd_def.get("command")
            desc = cmd_def.get("description", "No description provided")
            base_description += f"- `{cmd}`: {desc}\n"
        base_description += "\nYou can also use variations of these commands with different arguments if needed.\n"
    else:
        base_description += """
            Common use cases:
            - Check file contents (cat, head, tail, grep)
            - Examine git status or diffs (git status, git diff, git log)
            - Run tests or builds (npm test, pytest, make)
            - Check system information (ls, find, ps, df)
        """

    base_description += """
        Do NOT use this for:
        - Destructive operations (rm, mv, dd)
        - Privilege escalation (sudo, su)
        - Network operations (curl, wget) unless explicitly allowed
        - Writing or modifying files (>, >>, vim, nano)

        The command will be validated against allowlists/denylists before execution.
    """

    return {
        "type": "function",
        "function": {
            "name": "execute_bash_command",
            "description": base_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute (e.g., 'git status', 'npm test', 'cat error.log')"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why this command is needed to answer the user's question"
                    }
                },
                "required": ["command", "reason"]
            }
        }
    }

# Example generated tool with available_commands defined:
EXAMPLE_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_bash_command",
        "description": """
            Execute a bash command to gather information needed to answer the user's question.

            Available commands:
            - `git status`: Show the working tree status - which files are modified, staged, or untracked
            - `git diff`: Show changes between commits, commit and working tree, etc.
            - `git log --oneline -10`: Show the last 10 commit messages in compact format
            - `npm test`: Run the project's test suite and show test results
            - `npm run build`: Build the project and show any compilation errors

            You can also use variations of these commands with different arguments if needed.

            Do NOT use this for:
            - Destructive operations (rm, mv, dd)
            - Privilege escalation (sudo, su)
            - Network operations (curl, wget) unless explicitly allowed
            - Writing or modifying files (>, >>, vim, nano)

            The command will be validated against allowlists/denylists before execution.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "reason": {
                    "type": "string",
                    "description": "Why this command is needed"
                }
            },
            "required": ["command", "reason"]
        }
    }
}
```

**4. Agentic Execution Loop**

```python
def execute_with_dynamic_commands(prompt, config):
    messages = [{"role": "user", "content": prompt}]
    commands_executed = 0
    max_iterations = config.get("max_commands", 10)

    while commands_executed < max_iterations:
        # Call LLM with tool definition
        response = litellm.completion(
            model=config["model"],
            messages=messages,
            tools=[COMMAND_EXECUTION_TOOL],
            tool_choice="auto"
        )

        # Check if LLM wants to execute a command
        if response.choices[0].finish_reason == "tool_calls":
            tool_call = response.choices[0].message.tool_calls[0]
            command = json.loads(tool_call.function.arguments)["command"]
            reason = json.loads(tool_call.function.arguments)["reason"]

            # Validate command against allowlist/denylist
            if not is_command_allowed(command, config):
                return f"Error: Command '{command}' is not allowed"

            # Optional: Confirm with user
            if config.get("require_confirmation"):
                if not confirm_command_execution(command, reason):
                    return "Command execution denied by user"

            # Execute command
            result = execute_command(command, timeout=config.get("timeout", 30))

            # Add tool call and result to message history
            messages.append(response.choices[0].message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

            commands_executed += 1
        else:
            # LLM has finished reasoning and provided final answer
            return response.choices[0].message.content

    return "Error: Maximum command execution limit reached"
```

**5. Safety Mechanisms**

```python
def is_command_allowed(command: str, config: dict) -> bool:
    """Validate command against available_commands, allowlist, and denylist."""

    # Check denylist first (takes precedence over everything)
    denylist = config.get("dynamic_commands", {}).get("deny", [])
    for pattern in denylist:
        if fnmatch.fnmatch(command, pattern):
            return False

    # Check available_commands (structured definitions with descriptions)
    available_commands = config.get("dynamic_commands", {}).get("available_commands", None)
    if available_commands is not None:
        for cmd_def in available_commands:
            cmd_pattern = cmd_def.get("command", "")
            # Exact match or pattern match
            if command == cmd_pattern or fnmatch.fnmatch(command, cmd_pattern + "*"):
                return True
        # If available_commands is defined but command not found, still check allowlist
        # This allows combining both approaches

    # Check allowlist if defined (simple wildcard patterns)
    allowlist = config.get("dynamic_commands", {}).get("allow", None)
    if allowlist is not None:
        for pattern in allowlist:
            if fnmatch.fnmatch(command, pattern):
                return True

    # If either available_commands or allowlist was defined, don't use defaults
    if available_commands is not None or allowlist is not None:
        return False

    # Default: allow safe read-only commands when no explicit configuration
    SAFE_DEFAULT_COMMANDS = [
        "git status*", "git log*", "git diff*", "git show*",
        "ls*", "cat*", "head*", "tail*", "grep*", "find*",
        "npm test*", "pytest*", "make test*",
        "df*", "ps*", "whoami", "pwd"
    ]

    for pattern in SAFE_DEFAULT_COMMANDS:
        if fnmatch.fnmatch(command, pattern):
            return True

    return False  # Not in safe defaults
```

**6. Output Format**

When `--allow-commands` is enabled, CLLM will show:

```
$ cllm "Why is my build failing?" --allow-commands

[Executing: npm run build]
Reason: Check build output for errors

> npm run build
Error: Module not found: 'react-router'
...

[Executing: cat package.json]
Reason: Verify react-router dependency

{
  "dependencies": {
    "react": "^18.0.0"
    // react-router is missing
  }
}

Your build is failing because react-router is not listed in your
package.json dependencies. To fix this, run:

npm install react-router-dom

This will add the missing dependency and resolve the import error.
```

**7. Benefits of Command Descriptions**

Using structured `available_commands` with descriptions provides several advantages over simple allowlist patterns:

**Improved LLM Decision-Making:**
- The LLM can see exactly what each command does before choosing it
- Reduces trial-and-error by helping the LLM select the right command on the first try
- Example: LLM knows `git diff` shows changes vs `git log` shows history

**Better User Experience:**
- More accurate command selection means faster answers
- Fewer unnecessary commands executed (saves time and tokens)
- LLM explains why it chose each command (transparency)

**Self-Documenting Configuration:**
- Team members can understand what commands are available at a glance
- Easy to audit security implications (see exactly what each command does)
- Reduces need for separate documentation

**Flexibility with Guidance:**
- LLM can use variations (e.g., `git log --oneline -5` based on `git log --oneline -10`)
- Descriptions guide usage patterns without being overly restrictive
- Combines structure with adaptability

**Critical for Custom Scripts and Uncommon Commands:**
- **Parameter guidance**: Descriptions explain required/optional parameters for bash scripts
  - Example: `"./scripts/analyze-logs.sh <log_file>"` with description showing usage
- **Tool-specific syntax**: Uncommon commands (jq, fd, rg) need syntax examples
  - Example: `"jq '.dependencies' package.json"` with description explaining how to modify the query
- **Prevents errors**: LLM knows how to invoke commands correctly on the first try
- **Enables complex workflows**: LLM can chain custom scripts intelligently
- **Team-specific tooling**: Document internal tools without external docs

**Example Comparison:**

Without descriptions (simple allowlist):
```yaml
allow:
  - "git*"             # Which git command? For what purpose?
  - "npm*"             # Build? Test? Install?
  - "./scripts/*"      # What do these scripts do? What parameters?
  - "jq*"              # How to use jq syntax?
```

**Problem**: LLM must guess which command to use and how to invoke it. May try `npm install` when `npm test` was needed, or invoke `./scripts/deploy.sh` without required parameters.

With descriptions (structured):
```yaml
available_commands:
  - command: "git status"
    description: "Show which files are modified, staged, or untracked"

  - command: "git diff"
    description: "Show changes between commits or working tree"

  - command: "npm test"
    description: "Run the test suite and show results"

  - command: "npm run build"
    description: "Build the project and show compilation errors"

  - command: "./scripts/check-deps.sh"
    description: "Check for outdated dependencies. Usage: ./scripts/check-deps.sh [--fix] to auto-update"

  - command: "jq '.dependencies' package.json"
    description: "Extract dependencies from package.json using jq. Change '.dependencies' to '.devDependencies' for dev deps"
```

**Benefit**: The LLM can now make informed decisions:
- For "Why is my build failing?", it will choose `npm run build` (not `npm test`) because the description indicates it shows compilation errors
- For "Check if dependencies are outdated", it will use `./scripts/check-deps.sh` and know it can add `--fix` to auto-update
- For "What are my dev dependencies?", it will use `jq '.devDependencies' package.json` by adapting the provided example

**8. Integration with Existing Features**

- **ADR-0011 (Context Injection)**: Pre-configured context commands run *before* LLM processing; dynamic commands run *during* LLM processing
- **ADR-0003 (Cllmfile)**: Dynamic command settings configured in Cllmfile.yml with standard precedence rules
- **ADR-0007 (Conversations)**: Command execution history stored in conversation threads; LLM can reference previous commands

**9. Provider Compatibility**

Tool calling support across LiteLLM providers:

| Provider | Tool Calling Support | Notes |
|----------|---------------------|-------|
| OpenAI (GPT-4, GPT-3.5) | ✅ Yes | Native function calling |
| Anthropic (Claude 3+) | ✅ Yes | Native tool use |
| Google (Gemini) | ✅ Yes | Function calling |
| Groq | ✅ Yes | Via function calling API |
| Cohere | ✅ Yes | Tool use API |
| Mistral | ✅ Yes | Function calling |
| Local models (Ollama) | ⚠️ Partial | Depends on model |
| Azure OpenAI | ✅ Yes | Same as OpenAI |

For providers without tool calling, CLLM will show:

```text
Error: Dynamic command execution requires a model with tool calling support.
Supported models: gpt-4, gpt-3.5-turbo, claude-3-opus, gemini-pro, etc.

Try: cllm "your prompt" --model gpt-4 --allow-commands
```

**10. Best Practices for Command Descriptions**

When writing command descriptions, especially for custom scripts and uncommon tools:

**1. Include What AND How:**
- State what the command does (purpose)
- Explain how to use it (parameters, syntax)
- Provide examples when syntax is non-obvious

**2. Document Parameters:**
```yaml
# Bad: Missing parameter guidance
- command: "./scripts/deploy.sh"
  description: "Deploy the application"

# Good: Clear parameter requirements
- command: "./scripts/deploy.sh <environment>"
  description: "Deploy the application to specified environment. Requires: staging, production, or dev. Example: ./scripts/deploy.sh staging"
```

**3. Show Syntax Variations:**
```yaml
# Good: Helps LLM adapt the command
- command: "jq '.dependencies' package.json"
  description: "Extract dependencies from package.json using jq (JSON processor). For dev dependencies use '.devDependencies', for peer dependencies use '.peerDependencies'"
```

**4. Explain Optional Flags:**
```yaml
# Good: Documents optional behavior
- command: "./scripts/check-deps.sh"
  description: "Check for outdated dependencies and security vulnerabilities. Add --fix flag to automatically update packages. Add --verbose for detailed output"
```

**5. Clarify Tool-Specific Syntax:**
```yaml
# Good: Explains uncommon command usage
- command: "fd -e py -x wc -l"
  description: "Count total lines in all Python files using fd (fast find alternative). Use 'fd -e js' for JavaScript, 'fd -e rs' for Rust. The -x flag executes wc -l on each match"
```

**6. Indicate Side Effects:**
```yaml
# Good: Warns about non-read-only operations
- command: "./scripts/cleanup-logs.sh"
  description: "Archive and compress logs older than 30 days. WARNING: This modifies the filesystem by moving files to logs/archive/"
```

**7. Mention Common Pitfalls:**
```yaml
# Good: Prevents common errors
- command: "docker ps --format '{{.Names}}'"
  description: "List running Docker container names. Note: Single quotes required to prevent shell expansion. Returns empty if Docker daemon is not running"
```

**8. Keep It Concise:**
- Aim for 1-3 sentences
- Focus on essentials (what, required params, key options)
- Avoid redundant information already in the command itself

**Example: Well-Documented Custom Script**
```yaml
- command: "./scripts/db-backup.sh <database_name> [--compress]"
  description: |
    Create a backup of the specified database.
    Required: database_name (e.g., 'production', 'staging')
    Optional: --compress flag to gzip the backup file
    Output: backup file in ./backups/ directory
    Example: ./scripts/db-backup.sh production --compress
```

---

## AI-Specific Extensions

### AI Guidance Level

**Flexible**: Core functionality (tool calling integration, command validation, agentic loop) should follow this spec. Implementation details (error messages, output formatting, confirmation prompts) can be adapted for better UX.

### AI Tool Preferences

- **Preferred AI tools**: Claude Code for implementation
- **Model parameters**: Default settings
- **Special instructions**:
  - Use LiteLLM's native tool calling API (don't implement custom parsing)
  - Follow existing patterns from ADR-0011 for command execution
  - Ensure thread-safety for parallel command execution
  - Use `subprocess` with timeout protection

### Test Expectations

**Unit tests:**
- Parse `allow_dynamic_commands` and `dynamic_commands` from Cllmfile.yml
- Parse `available_commands` with descriptions from config
- Validate `--allow-commands` CLI flag
- Command allowlist/denylist validation logic (including `available_commands`)
- Tool definition generation (with and without command descriptions)
- Verify descriptions are properly included in tool definitions

**Integration tests:**
- LiteLLM tool calling with mock LLM responses
- Agentic loop execution (multiple tool calls)
- Command execution and output capture
- Conversation history with tool calls (ADR-0007)
- Timeout handling
- Command validation with structured `available_commands`
- Tool definition generation includes command descriptions in prompt

**End-to-end tests:**
- Real workflow: "Why is my build failing?" → executes `npm run build` → analyzes output
- Real workflow: "What changed in the last commit?" → executes `git show` → summarizes
- Safety: Attempt denied command → proper error message
- Confirmation: User denies command → graceful exit
- Command selection accuracy: Verify LLM chooses correct command when descriptions are provided
- Verify LLM can use command variations (e.g., `git log -5` based on `git log --oneline -10`)

**Provider compatibility tests:**
- Test with OpenAI (gpt-4)
- Test with Anthropic (claude-3-opus)
- Test with Google (gemini-pro)
- Test with non-tool-calling model → proper error message

### Dependencies

- **Related ADRs**:
  - ADR-0011 (Dynamic Context Injection) - Complementary feature (pre-configured vs. LLM-driven)
  - ADR-0003 (Cllmfile Configuration) - Extends config schema
  - ADR-0007 (Conversation Threading) - Tool call history stored in conversations
  - ADR-0002 (LiteLLM Abstraction) - Uses LiteLLM's tool calling API
- **System components**:
  - `src/cllm/config.py` - Parse `dynamic_commands` from Cllmfile
  - `src/cllm/cli.py` - Add `--allow-commands`, `--command-allow`, `--command-deny`, `--confirm-commands` flags
  - `src/cllm/tools.py` (new) - Tool definitions and command validation
  - `src/cllm/agent.py` (new) - Agentic execution loop
  - `src/cllm/context.py` (from ADR-0011) - Shared command execution logic
- **External dependencies**:
  - LiteLLM (already a dependency) - Tool calling support
  - Python `subprocess` module (stdlib)
  - Python `fnmatch` module (stdlib) - Pattern matching for allowlist/denylist

### Timeline

- **Implementation deadline**: None (feature proposal)
- **First review**: After initial implementation PR
- **Revision triggers**:
  - Security vulnerabilities in command validation
  - LiteLLM changes to tool calling API
  - User feedback on safety mechanisms
  - Provider compatibility issues

### Risk Assessment

#### Technical Risks

- **Tool calling API differences across providers**:
  - *Mitigation*: Use LiteLLM's unified interface, test with multiple providers, document provider-specific limitations
- **Agentic loop divergence (LLM executes unnecessary commands)**:
  - *Mitigation*: Set `max_commands` limit, monitor token usage, provide clear tool descriptions
- **Command execution failures**:
  - *Mitigation*: Timeout protection, error message injection into LLM context, fallback strategies
- **Token usage explosion**:
  - *Mitigation*: Limit max iterations, provide `--no-allow-commands` to disable, document cost implications

#### Business Risks

- **Security concerns (arbitrary command execution)**:
  - *Mitigation*: Allowlist/denylist validation, user confirmation option, safe defaults, clear documentation of risks
- **User trust issues (LLM executing commands without visibility)**:
  - *Mitigation*: Show all executed commands, require `--allow-commands` opt-in, provide `--confirm-commands` for interactive approval
- **Cost implications (increased token usage)**:
  - *Mitigation*: Document token usage patterns, provide cost estimates, make feature opt-in

### Human Review

- **Review required**: Before implementation (design review) + after implementation (security review)
- **Reviewers**: Project maintainers, security-focused users, LLM tool calling experts
- **Approval criteria**:
  - Security model prevents dangerous command execution
  - Allowlist/denylist validation is robust
  - Tool calling integration works across major providers
  - Documentation clearly explains risks and safety mechanisms
  - Tests cover failure modes, edge cases, and attack vectors

### Feedback Log

*To be filled after implementation*

- **Implementation date**: TBD
- **Actual outcomes**: TBD
- **Challenges encountered**: TBD
- **Lessons learned**: TBD
- **Suggested improvements**: TBD
