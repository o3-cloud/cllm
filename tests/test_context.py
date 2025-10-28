"""
Unit tests for context command execution (ADR-0011).

Tests dynamic context injection via command execution.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from cllm.context import (
    ContextCommand,
    CommandResult,
    FailureMode,
    execute_commands,
    format_context_block,
    format_error_block,
    inject_context,
    parse_context_commands,
)


class TestContextCommand:
    """Tests for ContextCommand dataclass and factory methods."""

    def test_from_dict_minimal(self):
        """Test creating ContextCommand from minimal dict."""
        data = {"name": "Test Command", "command": "echo hello"}

        cmd = ContextCommand.from_dict(data)

        assert cmd.name == "Test Command"
        assert cmd.command == "echo hello"
        assert cmd.on_failure == FailureMode.WARN  # default
        assert cmd.timeout == 10  # default

    def test_from_dict_full(self):
        """Test creating ContextCommand with all fields."""
        data = {
            "name": "Git Status",
            "command": "git status",
            "on_failure": "fail",
            "timeout": 5,
        }

        cmd = ContextCommand.from_dict(data)

        assert cmd.name == "Git Status"
        assert cmd.command == "git status"
        assert cmd.on_failure == FailureMode.FAIL
        assert cmd.timeout == 5

    def test_from_dict_missing_name(self):
        """Test error when name is missing."""
        data = {"command": "echo test"}

        with pytest.raises(ValueError, match="missing required field: 'name'"):
            ContextCommand.from_dict(data)

    def test_from_dict_missing_command(self):
        """Test error when command is missing."""
        data = {"name": "Test"}

        with pytest.raises(ValueError, match="missing required field: 'command'"):
            ContextCommand.from_dict(data)

    def test_from_dict_invalid_on_failure(self):
        """Test error with invalid on_failure value."""
        data = {"name": "Test", "command": "echo test", "on_failure": "invalid"}

        with pytest.raises(ValueError, match="Invalid on_failure value"):
            ContextCommand.from_dict(data)

    def test_from_dict_case_insensitive_on_failure(self):
        """Test that on_failure is case-insensitive."""
        data = {"name": "Test", "command": "echo test", "on_failure": "WARN"}

        cmd = ContextCommand.from_dict(data)

        assert cmd.on_failure == FailureMode.WARN


class TestExecuteCommands:
    """Tests for command execution."""

    def test_execute_simple_command(self):
        """Test executing a simple successful command."""
        cmd = ContextCommand(
            name="Echo Test", command="echo 'hello world'", timeout=5
        )

        results = execute_commands([cmd])

        assert len(results) == 1
        assert results[0].name == "Echo Test"
        assert results[0].success is True
        assert "hello world" in results[0].output
        assert results[0].error_message is None

    def test_execute_failing_command(self):
        """Test executing a command that fails."""
        cmd = ContextCommand(
            name="Failing Command", command="exit 1", timeout=5
        )

        results = execute_commands([cmd])

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error_message is not None
        assert "exited with code 1" in results[0].error_message

    def test_execute_nonexistent_command(self):
        """Test executing a command that doesn't exist."""
        cmd = ContextCommand(
            name="Bad Command", command="this_command_does_not_exist_xyz", timeout=5
        )

        results = execute_commands([cmd])

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error_message is not None

    def test_execute_command_with_timeout(self):
        """Test that long-running commands are terminated on timeout."""
        cmd = ContextCommand(
            name="Slow Command", command="sleep 10", timeout=1  # 1 second timeout
        )

        results = execute_commands([cmd])

        assert len(results) == 1
        assert results[0].success is False
        assert "timed out" in results[0].error_message.lower()

    def test_execute_multiple_commands_parallel(self):
        """Test executing multiple commands in parallel."""
        commands = [
            ContextCommand(name="Cmd 1", command="echo 'first'", timeout=5),
            ContextCommand(name="Cmd 2", command="echo 'second'", timeout=5),
            ContextCommand(name="Cmd 3", command="echo 'third'", timeout=5),
        ]

        results = execute_commands(commands, parallel=True)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].name == "Cmd 1"
        assert results[1].name == "Cmd 2"
        assert results[2].name == "Cmd 3"

    def test_execute_multiple_commands_sequential(self):
        """Test executing multiple commands sequentially."""
        commands = [
            ContextCommand(name="Cmd 1", command="echo 'first'", timeout=5),
            ContextCommand(name="Cmd 2", command="echo 'second'", timeout=5),
        ]

        results = execute_commands(commands, parallel=False)

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_execute_empty_command_list(self):
        """Test executing empty command list."""
        results = execute_commands([])

        assert results == []


class TestFormatFunctions:
    """Tests for formatting functions."""

    def test_format_context_block_with_output(self):
        """Test formatting a successful command result."""
        result = CommandResult(
            name="Git Status", output="M src/file.py\n?? new.py", success=True
        )

        formatted = format_context_block(result)

        assert "--- Context: Git Status ---" in formatted
        assert "M src/file.py" in formatted
        assert "?? new.py" in formatted
        assert "--- End Context ---" in formatted

    def test_format_context_block_no_output(self):
        """Test formatting when command has no output."""
        result = CommandResult(name="Empty Command", output="", success=True)

        formatted = format_context_block(result)

        assert "--- Context: Empty Command ---" in formatted
        assert "(no output)" in formatted
        assert "--- End Context ---" in formatted

    def test_format_error_block(self):
        """Test formatting an error result."""
        result = CommandResult(
            name="Failed Command",
            output="some partial output",
            success=False,
            error_message="Command exited with code 1",
        )

        formatted = format_error_block(result)

        assert "--- Context Error: Failed Command ---" in formatted
        assert "Command exited with code 1" in formatted
        assert "Partial output:" in formatted
        assert "some partial output" in formatted
        assert "--- End Context ---" in formatted

    def test_format_error_block_no_output(self):
        """Test formatting error without partial output."""
        result = CommandResult(
            name="Failed Command",
            output="",
            success=False,
            error_message="Timeout error",
        )

        formatted = format_error_block(result)

        assert "--- Context Error: Failed Command ---" in formatted
        assert "Timeout error" in formatted
        assert "Partial output:" not in formatted


class TestInjectContext:
    """Tests for inject_context main function."""

    def test_inject_context_success(self):
        """Test successful context injection."""
        prompt = "Analyze this code"
        commands = [
            ContextCommand(name="Git Status", command="echo 'M file.py'", timeout=5)
        ]

        result = inject_context(prompt, commands)

        assert "--- Context: Git Status ---" in result
        assert "M file.py" in result
        assert "--- End Context ---" in result
        assert "Analyze this code" in result
        # Context should come before prompt
        assert result.index("Git Status") < result.index("Analyze this code")

    def test_inject_context_multiple_commands(self):
        """Test injecting multiple context blocks."""
        prompt = "Debug this"
        commands = [
            ContextCommand(name="Cmd 1", command="echo 'output1'", timeout=5),
            ContextCommand(name="Cmd 2", command="echo 'output2'", timeout=5),
        ]

        result = inject_context(prompt, commands)

        assert "--- Context: Cmd 1 ---" in result
        assert "output1" in result
        assert "--- Context: Cmd 2 ---" in result
        assert "output2" in result
        assert "Debug this" in result

    def test_inject_context_with_failure_warn(self):
        """Test context injection when command fails with on_failure=warn."""
        prompt = "Analyze"
        commands = [
            ContextCommand(
                name="Failing Cmd",
                command="exit 1",
                on_failure=FailureMode.WARN,
                timeout=5,
            )
        ]

        result = inject_context(prompt, commands)

        # Should include error block
        assert "--- Context Error: Failing Cmd ---" in result
        assert "exited with code 1" in result
        assert "Analyze" in result

    def test_inject_context_with_failure_ignore(self):
        """Test context injection when command fails with on_failure=ignore."""
        prompt = "Analyze"
        commands = [
            ContextCommand(
                name="Failing Cmd",
                command="exit 1",
                on_failure=FailureMode.IGNORE,
                timeout=5,
            )
        ]

        result = inject_context(prompt, commands)

        # Should NOT include error block
        assert "--- Context Error:" not in result
        assert "Failing Cmd" not in result
        # Just return original prompt
        assert result == prompt

    def test_inject_context_with_failure_fail(self):
        """Test context injection when command fails with on_failure=fail."""
        prompt = "Analyze"
        commands = [
            ContextCommand(
                name="Failing Cmd",
                command="exit 1",
                on_failure=FailureMode.FAIL,
                timeout=5,
            )
        ]

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Context command 'Failing Cmd' failed"):
            inject_context(prompt, commands)

    def test_inject_context_empty_commands(self):
        """Test that empty command list returns original prompt."""
        prompt = "Original prompt"

        result = inject_context(prompt, [])

        assert result == prompt


class TestParseContextCommands:
    """Tests for parsing context_commands from config."""

    def test_parse_empty_config(self):
        """Test parsing config without context_commands."""
        config = {"model": "gpt-4", "temperature": 0.7}

        commands = parse_context_commands(config)

        assert commands == []

    def test_parse_valid_commands(self):
        """Test parsing valid context_commands."""
        config = {
            "model": "gpt-4",
            "context_commands": [
                {"name": "Git Status", "command": "git status"},
                {
                    "name": "Test Results",
                    "command": "pytest",
                    "on_failure": "ignore",
                    "timeout": 30,
                },
            ],
        }

        commands = parse_context_commands(config)

        assert len(commands) == 2
        assert commands[0].name == "Git Status"
        assert commands[0].command == "git status"
        assert commands[0].on_failure == FailureMode.WARN  # default
        assert commands[1].name == "Test Results"
        assert commands[1].command == "pytest"
        assert commands[1].on_failure == FailureMode.IGNORE
        assert commands[1].timeout == 30

    def test_parse_invalid_commands_not_list(self):
        """Test error when context_commands is not a list."""
        config = {"context_commands": "not a list"}

        with pytest.raises(ValueError, match="context_commands must be a list"):
            parse_context_commands(config)

    def test_parse_invalid_command_not_dict(self):
        """Test error when command entry is not a dict."""
        config = {"context_commands": ["not a dict"]}

        with pytest.raises(ValueError, match="context_commands\\[0\\] must be a dictionary"):
            parse_context_commands(config)

    def test_parse_invalid_command_missing_field(self):
        """Test error when command is missing required field."""
        config = {"context_commands": [{"name": "Test"}]}  # missing 'command'

        with pytest.raises(ValueError, match="context_commands\\[0\\]"):
            parse_context_commands(config)
