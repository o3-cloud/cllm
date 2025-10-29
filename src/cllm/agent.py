"""Agentic execution loop for dynamic command execution.

Implements ADR-0013: LLM-Driven Dynamic Command Execution
Provides functionality for the LLM to dynamically choose and execute commands.
"""

import json
import sys
from typing import Any, Dict, List

import litellm

from .context import ContextCommand, execute_commands
from .tools import CommandValidationError, generate_command_tool, validate_command


class AgentExecutionError(Exception):
    """Raised when the agentic execution loop encounters an error."""

    pass


def execute_single_command(command: str, timeout: int = 30) -> str:
    """Execute a single command and return its output.

    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds

    Returns:
        Command output (stdout + stderr)

    Raises:
        AgentExecutionError: If command execution fails
    """
    # Create a ContextCommand object to reuse existing execution logic
    ctx_cmd = ContextCommand(
        name="Dynamic Command",
        command=command,
        timeout=timeout,
    )

    # Execute the command
    results = execute_commands([ctx_cmd], cwd=None, parallel=False)

    if not results:
        raise AgentExecutionError("No command result returned")

    result = results[0]

    if not result.success:
        error_msg = result.error_message or "Unknown error"
        if result.output:
            return f"Error: {error_msg}\n\nPartial output:\n{result.output}"
        return f"Error: {error_msg}"

    return result.output if result.output else "(no output)"


def confirm_command_execution(command: str, reason: str) -> bool:
    """Prompt user to confirm command execution.

    Args:
        command: The command to be executed
        reason: LLM's explanation of why the command is needed

    Returns:
        True if user approves, False otherwise
    """
    print("\n[Command Request]", file=sys.stderr)
    print(f"Command: {command}", file=sys.stderr)
    print(f"Reason: {reason}", file=sys.stderr)
    print("\nAllow execution? [y/N]: ", file=sys.stderr, end="", flush=True)

    try:
        response = input().strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        return False


def execute_with_dynamic_commands(
    prompt: str,
    config: Dict[str, Any],
    require_confirmation: bool = False,
    verbose: bool = False,
    schema: Dict[str, Any] | None = None,
) -> str:
    """Execute LLM call with dynamic command execution capability.

    This implements the agentic execution loop:
    1. Call LLM with tool definition
    2. Check if LLM wants to execute a command
    3. Validate and execute the command
    4. Feed result back to LLM
    5. Repeat until LLM provides final answer

    Implements ADR-0014: JSON Structured Output with --allow-commands

    Args:
        prompt: User's prompt/question
        config: Configuration dictionary
        require_confirmation: If True, prompt user before each command execution
        verbose: If True, print execution details to stderr
        schema: Optional JSON schema for structured output (ADR-0014)

    Returns:
        Final LLM response text (conforming to schema if provided)

    Raises:
        AgentExecutionError: If execution loop fails
        CommandValidationError: If a command fails validation
    """
    # Get dynamic commands configuration
    dynamic_commands = config.get("dynamic_commands", {})
    max_commands = dynamic_commands.get("max_commands", 10)
    command_timeout = dynamic_commands.get("timeout", 30)

    # Generate tool definition
    tool = generate_command_tool(config)

    # Build initial messages
    messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]

    # Add system message if configured
    if "default_system_message" in config:
        messages.insert(0, {"role": "system", "content": config["default_system_message"]})

    commands_executed = 0

    # Agentic execution loop
    while commands_executed < max_commands:
        # Call LLM with tool definition
        try:
            # Prepare kwargs for litellm.completion
            kwargs = {
                "model": config.get("model", "gpt-4"),
                "messages": messages,
                "tools": [tool],
                "tool_choice": "auto",
                "temperature": config.get("temperature"),
                "max_tokens": config.get("max_tokens"),
                "timeout": config.get("timeout"),
                "num_retries": config.get("num_retries"),
                "fallbacks": config.get("fallbacks"),
            }

            # Add response_format for structured output if schema is present (ADR-0014)
            if schema is not None:
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response_schema",
                        "schema": schema,
                    },
                }

            response = litellm.completion(**kwargs)
        except Exception as e:
            raise AgentExecutionError(f"LLM API call failed: {e}")

        # Extract response
        choice = response.choices[0]
        message = choice.message

        # Check if LLM wants to execute commands
        if choice.finish_reason == "tool_calls" and hasattr(message, "tool_calls"):
            # Add the assistant message with all tool calls first
            messages.append(message.model_dump())

            # Process each tool call
            for tool_call in message.tool_calls:
                # Parse tool call arguments
                try:
                    args = json.loads(tool_call.function.arguments)
                    command = args.get("command", "")
                    reason = args.get("reason", "No reason provided")
                except (json.JSONDecodeError, KeyError) as e:
                    # Add error response for this tool call
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Failed to parse tool call arguments: {e}",
                    })
                    continue

                if verbose:
                    print(f"\n[Executing: {command}]", file=sys.stderr)
                    print(f"Reason: {reason}\n", file=sys.stderr)

                # Validate command
                try:
                    validate_command(command, config)
                except CommandValidationError as e:
                    # Return error to LLM so it can try a different approach
                    error_result = f"Command validation failed: {e}"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": error_result,
                    })
                    continue

                # Optional user confirmation
                if require_confirmation:
                    if not confirm_command_execution(command, reason):
                        return "Command execution denied by user."

                # Execute command
                try:
                    output = execute_single_command(command, timeout=command_timeout)
                except AgentExecutionError as e:
                    output = f"Execution failed: {e}"

                if verbose:
                    print(f"Output:\n{output}\n", file=sys.stderr)

                # Add tool result to message history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": output,
                })

                commands_executed += 1

                # Check if we've hit the max commands limit
                if commands_executed >= max_commands:
                    break

        elif choice.finish_reason == "stop":
            # LLM has finished reasoning and provided final answer
            if hasattr(message, "content") and message.content:
                return message.content
            else:
                raise AgentExecutionError("LLM returned empty response")

        else:
            # Unexpected finish reason
            if hasattr(message, "content") and message.content:
                return message.content
            else:
                raise AgentExecutionError(
                    f"Unexpected finish reason: {choice.finish_reason}"
                )

    # Max iterations reached
    raise AgentExecutionError(
        f"Maximum command execution limit reached ({max_commands} commands). "
        f"The LLM may be stuck in a loop or the task requires more commands than allowed. "
        f"Increase max_commands in your configuration if needed."
    )
