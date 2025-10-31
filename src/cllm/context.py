"""
Context command execution for dynamic context injection.

Implements ADR-0011: Dynamic Context Injection via Command Execution
Provides functionality to execute shell commands and inject their output
into LLM prompts for enhanced context-aware interactions.
"""

import asyncio
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .templates import (
    TemplateError,
    get_available_variables_description,
    render_command_template,
)


class FailureMode(Enum):
    """How to handle command execution failures."""

    WARN = "warn"  # Include error message in context
    IGNORE = "ignore"  # Skip this command's output
    FAIL = "fail"  # Abort LLM call with error


@dataclass
class ContextCommand:
    """
    A command to execute for context injection.

    Attributes:
        name: Human-readable label for the context (e.g., "Git Status")
        command: Shell command to execute (e.g., "git status --short")
        on_failure: How to handle execution failures (default: WARN)
        timeout: Maximum execution time in seconds (default: 10)
    """

    name: str
    command: str
    on_failure: FailureMode = FailureMode.WARN
    timeout: int = 10

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextCommand":
        """
        Create ContextCommand from dictionary (e.g., from Cllmfile.yml).

        Args:
            data: Dictionary with keys: name, command, on_failure (optional), timeout (optional)

        Returns:
            ContextCommand instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if "name" not in data:
            raise ValueError("ContextCommand missing required field: 'name'")
        if "command" not in data:
            raise ValueError("ContextCommand missing required field: 'command'")

        # Parse on_failure
        on_failure_str = data.get("on_failure", "warn")
        try:
            on_failure = FailureMode(on_failure_str.lower())
        except ValueError as err:
            raise ValueError(
                f"Invalid on_failure value: '{on_failure_str}'. "
                f"Must be one of: warn, ignore, fail"
            ) from err

        return cls(
            name=data["name"],
            command=data["command"],
            on_failure=on_failure,
            timeout=data.get("timeout", 10),
        )


@dataclass
class CommandResult:
    """
    Result of executing a context command.

    Attributes:
        name: Name of the command (for labeling)
        output: Combined stdout/stderr output
        success: Whether command executed successfully
        error_message: Error message if command failed (None if successful)
    """

    name: str
    output: str
    success: bool
    error_message: Optional[str] = None


async def _execute_command_async(
    cmd: ContextCommand, cwd: Optional[Path] = None
) -> CommandResult:
    """
    Execute a command asynchronously with timeout protection.

    Args:
        cmd: ContextCommand to execute
        cwd: Working directory for command execution (defaults to current dir)

    Returns:
        CommandResult with execution output/error
    """
    try:
        # Execute command with timeout
        proc = await asyncio.create_subprocess_shell(
            cmd.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=cmd.timeout
            )
        except asyncio.TimeoutError:
            # Kill the process on timeout
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass  # Process already terminated

            return CommandResult(
                name=cmd.name,
                output="",
                success=False,
                error_message=f"Command timed out after {cmd.timeout} seconds",
            )

        # Combine stdout and stderr
        output = stdout.decode("utf-8", errors="replace")
        error_output = stderr.decode("utf-8", errors="replace")

        if proc.returncode == 0:
            # Success - combine both streams (some tools write to stderr even on success)
            combined_output = output
            if error_output.strip():
                combined_output += f"\n{error_output}"

            return CommandResult(
                name=cmd.name, output=combined_output.strip(), success=True
            )
        else:
            # Non-zero exit code
            combined_output = output
            if error_output.strip():
                combined_output += f"\n{error_output}"

            return CommandResult(
                name=cmd.name,
                output=combined_output.strip(),
                success=False,
                error_message=f"Command exited with code {proc.returncode}",
            )

    except Exception as e:
        return CommandResult(
            name=cmd.name,
            output="",
            success=False,
            error_message=f"Execution error: {str(e)}",
        )


def execute_commands(
    commands: List[ContextCommand],
    cwd: Optional[Path] = None,
    parallel: bool = True,
) -> List[CommandResult]:
    """
    Execute multiple context commands.

    Args:
        commands: List of ContextCommand objects to execute
        cwd: Working directory for command execution (defaults to current dir)
        parallel: Execute commands in parallel (default: True)

    Returns:
        List of CommandResult objects in same order as input commands
    """
    if not commands:
        return []

    async def _run_all():
        if parallel:
            # Execute all commands concurrently
            tasks = [_execute_command_async(cmd, cwd) for cmd in commands]
            return await asyncio.gather(*tasks)
        else:
            # Execute sequentially
            results = []
            for cmd in commands:
                result = await _execute_command_async(cmd, cwd)
                results.append(result)
            return results

    return asyncio.run(_run_all())


def format_context_block(result: CommandResult) -> str:
    """
    Format a command result as a labeled context block.

    Args:
        result: CommandResult to format

    Returns:
        Formatted string with context block markers

    Example:
        --- Context: Git Status ---
        M src/file.py
        ?? new-file.py
        --- End Context ---
    """
    if not result.output:
        return f"--- Context: {result.name} ---\n(no output)\n--- End Context ---"

    return f"--- Context: {result.name} ---\n{result.output}\n--- End Context ---"


def format_error_block(result: CommandResult) -> str:
    """
    Format a command error as a labeled error block.

    Args:
        result: CommandResult with error

    Returns:
        Formatted string with error block markers

    Example:
        --- Context Error: Git Status ---
        Command timed out after 10 seconds
        --- End Context ---
    """
    error_msg = result.error_message or "Unknown error"
    output_section = ""
    if result.output:
        output_section = f"\nPartial output:\n{result.output}"

    return f"--- Context Error: {result.name} ---\n{error_msg}{output_section}\n--- End Context ---"


def inject_context(
    prompt: str,
    commands: List[ContextCommand],
    cwd: Optional[Path] = None,
    parallel: bool = True,
    template_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Execute commands and inject their output into the prompt.

    This is the main entry point for context injection. It:
    1. Executes all commands (respecting on_failure settings)
    2. Formats output as labeled blocks
    3. Prepends context to the original prompt

    Args:
        prompt: Original user prompt
        commands: List of ContextCommand objects
        cwd: Working directory for command execution
        parallel: Execute commands in parallel (default: True)
        template_context: Optional variable context for template expansion (ADR-0012)

    Returns:
        Enhanced prompt with context blocks prepended

    Raises:
        RuntimeError: If any command with on_failure=FAIL fails
        TemplateError: If a command template cannot be rendered
    """
    if not commands:
        return prompt

    # Render command templates using provided context before execution
    rendered_commands: List[ContextCommand] = []
    context_values: Dict[str, Any] = template_context or {}

    for cmd in commands:
        try:
            rendered_command = render_command_template(cmd.command, context_values)
        except TemplateError as err:
            available_desc = get_available_variables_description(context_values)
            message = f"In context command '{cmd.name}': {err}"
            if available_desc:
                message = f"{message}\n\n{available_desc}"
            raise TemplateError(message) from err

        rendered_commands.append(replace(cmd, command=rendered_command))

    # Execute all commands
    results = execute_commands(rendered_commands, cwd=cwd, parallel=parallel)

    # Process results according to on_failure settings
    context_blocks = []
    for cmd, result in zip(rendered_commands, results):
        if result.success:
            # Success - always include output
            context_blocks.append(format_context_block(result))
        else:
            # Failure - handle according to on_failure setting
            if cmd.on_failure == FailureMode.FAIL:
                raise RuntimeError(
                    f"Context command '{cmd.name}' failed: {result.error_message}"
                )
            elif cmd.on_failure == FailureMode.WARN:
                # Include error in context
                context_blocks.append(format_error_block(result))
            # IGNORE: skip this command's output (do nothing)

    # Combine context blocks with original prompt
    if not context_blocks:
        # No successful context commands
        return prompt

    context_section = "\n\n".join(context_blocks)
    return f"{context_section}\n\n{prompt}"


def parse_context_commands(config: Dict[str, Any]) -> List[ContextCommand]:
    """
    Parse context_commands from configuration dictionary.

    Args:
        config: Configuration dictionary (from Cllmfile.yml)

    Returns:
        List of ContextCommand objects

    Raises:
        ValueError: If context_commands format is invalid
    """
    if "context_commands" not in config:
        return []

    commands_data = config["context_commands"]
    if not isinstance(commands_data, list):
        raise ValueError("context_commands must be a list")

    commands = []
    for i, cmd_data in enumerate(commands_data):
        if not isinstance(cmd_data, dict):
            raise ValueError(f"context_commands[{i}] must be a dictionary")

        try:
            cmd = ContextCommand.from_dict(cmd_data)
            commands.append(cmd)
        except ValueError as e:
            raise ValueError(f"context_commands[{i}]: {e}") from e

    return commands
