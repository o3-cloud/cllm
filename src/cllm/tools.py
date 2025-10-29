"""Tool definitions and command validation for dynamic command execution.

Implements ADR-0013: LLM-Driven Dynamic Command Execution
"""

import fnmatch
from typing import Any, Dict


class CommandValidationError(Exception):
    """Raised when a command fails validation checks."""

    pass


# Safe default commands (read-only operations)
SAFE_DEFAULT_COMMANDS = [
    "git status*",
    "git log*",
    "git diff*",
    "git show*",
    "git branch*",
    "ls*",
    "cat *",
    "head *",
    "tail *",
    "grep *",
    "find *",
    "npm test*",
    "pytest*",
    "make test*",
    "df*",
    "ps*",
    "whoami",
    "pwd",
    "echo *",
]


def generate_command_tool(config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate LiteLLM tool definition for command execution.

    The tool definition is dynamically built based on the configuration.
    If available_commands with descriptions is provided, those descriptions
    are included to help the LLM choose the right command.

    Args:
        config: Configuration dictionary with optional dynamic_commands section

    Returns:
        LiteLLM tool definition dictionary
    """
    base_description = (
        "Execute a bash command to gather information needed to answer the user's question.\n\n"
    )

    dynamic_commands = config.get("dynamic_commands", {})
    available_commands = dynamic_commands.get("available_commands", [])

    if available_commands:
        base_description += "Available commands:\n"
        for cmd_def in available_commands:
            if isinstance(cmd_def, dict):
                cmd = cmd_def.get("command", "")
                desc = cmd_def.get("description", "No description provided")
                base_description += f"- `{cmd}`: {desc}\n"
        base_description += (
            "\nYou can also use variations of these commands with different arguments if needed.\n\n"
        )
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
                        "description": "The bash command to execute (e.g., 'git status', 'npm test', 'cat error.log')",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why this command is needed to answer the user's question",
                    },
                },
                "required": ["command", "reason"],
            },
        },
    }


def is_command_allowed(command: str, config: Dict[str, Any]) -> bool:
    """Validate command against available_commands, allowlist, and denylist.

    Validation precedence:
    1. Denylist (highest precedence - blocks everything)
    2. Available commands (structured definitions with descriptions)
    3. Simple allowlist (wildcard patterns)
    4. Safe defaults (when no explicit configuration)

    Args:
        command: The command string to validate
        config: Configuration dictionary with optional dynamic_commands section

    Returns:
        True if command is allowed, False otherwise
    """
    dynamic_commands = config.get("dynamic_commands", {})

    # Check denylist first (takes precedence over everything)
    denylist = dynamic_commands.get("deny", [])
    for pattern in denylist:
        if fnmatch.fnmatch(command, pattern):
            return False

    # Check available_commands (structured definitions with descriptions)
    available_commands = dynamic_commands.get("available_commands", None)
    if available_commands is not None:
        for cmd_def in available_commands:
            if isinstance(cmd_def, dict):
                cmd_pattern = cmd_def.get("command", "")
                # Exact match or pattern match (allow variations)
                if command == cmd_pattern or fnmatch.fnmatch(
                    command, cmd_pattern + "*"
                ):
                    return True
        # If available_commands is defined but command not found, still check allowlist
        # This allows combining both approaches

    # Check allowlist if defined (simple wildcard patterns)
    allowlist = dynamic_commands.get("allow", None)
    if allowlist is not None:
        for pattern in allowlist:
            if fnmatch.fnmatch(command, pattern):
                return True

    # If either available_commands or allowlist was defined, don't use defaults
    if available_commands is not None or allowlist is not None:
        return False

    # Default: allow safe read-only commands when no explicit configuration
    for pattern in SAFE_DEFAULT_COMMANDS:
        if fnmatch.fnmatch(command, pattern):
            return True

    return False  # Not in safe defaults


def get_disallowed_reason(command: str, config: Dict[str, Any]) -> str:
    """Get a human-readable explanation of why a command was disallowed.

    Args:
        command: The command that was rejected
        config: Configuration dictionary

    Returns:
        Explanation string
    """
    dynamic_commands = config.get("dynamic_commands", {})

    # Check if blocked by denylist
    denylist = dynamic_commands.get("deny", [])
    for pattern in denylist:
        if fnmatch.fnmatch(command, pattern):
            return f"Command '{command}' matches denylist pattern: {pattern}"

    # Check if configuration defines allowlist/available_commands but command not in it
    available_commands = dynamic_commands.get("available_commands", None)
    allowlist = dynamic_commands.get("allow", None)

    if available_commands is not None or allowlist is not None:
        return (
            f"Command '{command}' is not in the configured allowed commands. "
            f"See dynamic_commands.available_commands or dynamic_commands.allow in your Cllmfile.yml"
        )

    # Otherwise, not in safe defaults
    return (
        f"Command '{command}' is not in the safe default command list. "
        f"To allow this command, add it to dynamic_commands.allow or dynamic_commands.available_commands "
        f"in your Cllmfile.yml"
    )


def validate_command(command: str, config: Dict[str, Any]) -> None:
    """Validate a command and raise an exception if not allowed.

    Args:
        command: The command to validate
        config: Configuration dictionary

    Raises:
        CommandValidationError: If command is not allowed
    """
    if not is_command_allowed(command, config):
        reason = get_disallowed_reason(command, config)
        raise CommandValidationError(reason)
