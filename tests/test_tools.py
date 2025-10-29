"""Tests for tools module (ADR-0013: LLM-Driven Dynamic Command Execution)."""

import pytest

from cllm.tools import (
    CommandValidationError,
    generate_command_tool,
    get_disallowed_reason,
    is_command_allowed,
    validate_command,
)


class TestIsCommandAllowed:
    """Tests for command validation logic."""

    def test_denylist_blocks_command(self):
        """Denylist should block commands matching patterns."""
        config = {"dynamic_commands": {"deny": ["rm *", "sudo *"]}}

        assert not is_command_allowed("rm -rf /", config)
        assert not is_command_allowed("sudo apt-get install", config)

    def test_denylist_takes_precedence_over_allowlist(self):
        """Denylist should take precedence over allowlist."""
        config = {
            "dynamic_commands": {
                "allow": ["git*"],
                "deny": ["git push --force"],
            }
        }

        assert is_command_allowed("git status", config)
        assert not is_command_allowed("git push --force", config)

    def test_available_commands_allows_exact_match(self):
        """Available commands should allow exact matches."""
        config = {
            "dynamic_commands": {
                "available_commands": [
                    {"command": "git status", "description": "Show status"},
                    {"command": "npm test", "description": "Run tests"},
                ]
            }
        }

        assert is_command_allowed("git status", config)
        assert is_command_allowed("npm test", config)

    def test_available_commands_allows_variations(self):
        """Available commands should allow variations with additional args."""
        config = {
            "dynamic_commands": {
                "available_commands": [
                    {"command": "git log", "description": "Show log"},
                ]
            }
        }

        assert is_command_allowed("git log", config)
        assert is_command_allowed("git log --oneline", config)
        assert is_command_allowed("git log -10", config)

    def test_available_commands_blocks_unlisted(self):
        """Available commands should block unlisted commands."""
        config = {
            "dynamic_commands": {
                "available_commands": [
                    {"command": "git status", "description": "Show status"},
                ]
            }
        }

        assert not is_command_allowed("rm -rf", config)
        assert not is_command_allowed("npm install", config)

    def test_simple_allowlist_with_wildcards(self):
        """Simple allowlist should support wildcard patterns."""
        config = {"dynamic_commands": {"allow": ["git*", "npm test*"]}}

        assert is_command_allowed("git status", config)
        assert is_command_allowed("git log", config)
        assert is_command_allowed("npm test", config)
        assert is_command_allowed("npm test --verbose", config)
        assert not is_command_allowed("rm -rf", config)

    def test_combining_available_commands_and_allowlist(self):
        """Both available_commands and allowlist should be checked."""
        config = {
            "dynamic_commands": {
                "available_commands": [
                    {"command": "git status", "description": "Status"},
                ],
                "allow": ["npm*"],
            }
        }

        assert is_command_allowed("git status", config)
        assert is_command_allowed("npm test", config)
        assert not is_command_allowed("rm -rf", config)

    def test_safe_defaults_when_no_config(self):
        """Safe default commands should be allowed when no config."""
        config = {}

        # Safe commands
        assert is_command_allowed("git status", config)
        assert is_command_allowed("cat file.txt", config)
        assert is_command_allowed("ls -la", config)
        assert is_command_allowed("pwd", config)

        # Unsafe commands
        assert not is_command_allowed("rm -rf", config)
        assert not is_command_allowed("sudo apt-get", config)

    def test_empty_dynamic_commands_uses_defaults(self):
        """Empty dynamic_commands config should use safe defaults."""
        config = {"dynamic_commands": {}}

        assert is_command_allowed("git status", config)
        assert not is_command_allowed("rm -rf", config)

    def test_explicit_config_disables_defaults(self):
        """Explicit config should disable safe defaults."""
        config = {"dynamic_commands": {"allow": ["npm*"]}}

        assert is_command_allowed("npm test", config)
        # git status is in safe defaults but not in explicit allowlist
        assert not is_command_allowed("git status", config)


class TestGenerateCommandTool:
    """Tests for tool definition generation."""

    def test_generates_basic_tool(self):
        """Should generate basic tool definition."""
        config = {}
        tool = generate_command_tool(config)

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "execute_bash_command"
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]
        assert tool["function"]["parameters"]["required"] == ["command", "reason"]

    def test_includes_available_commands_in_description(self):
        """Should include available commands in tool description."""
        config = {
            "dynamic_commands": {
                "available_commands": [
                    {"command": "git status", "description": "Show status"},
                    {"command": "npm test", "description": "Run tests"},
                ]
            }
        }
        tool = generate_command_tool(config)
        description = tool["function"]["description"]

        assert "git status" in description
        assert "Show status" in description
        assert "npm test" in description
        assert "Run tests" in description

    def test_handles_missing_description(self):
        """Should handle commands without descriptions gracefully."""
        config = {
            "dynamic_commands": {
                "available_commands": [
                    {"command": "git status"},  # No description
                ]
            }
        }
        tool = generate_command_tool(config)
        description = tool["function"]["description"]

        assert "git status" in description
        assert "No description provided" in description


class TestGetDisallowedReason:
    """Tests for disallowed reason explanations."""

    def test_explains_denylist_block(self):
        """Should explain when command is blocked by denylist."""
        config = {"dynamic_commands": {"deny": ["rm *"]}}
        reason = get_disallowed_reason("rm -rf /", config)

        assert "denylist" in reason.lower()
        assert "rm *" in reason

    def test_explains_not_in_allowlist(self):
        """Should explain when command is not in allowlist."""
        config = {"dynamic_commands": {"allow": ["git*"]}}
        reason = get_disallowed_reason("npm test", config)

        assert "not in the configured allowed commands" in reason

    def test_explains_not_in_safe_defaults(self):
        """Should explain when command is not in safe defaults."""
        config = {}
        reason = get_disallowed_reason("rm -rf", config)

        assert "not in the safe default command list" in reason


class TestValidateCommand:
    """Tests for command validation with exceptions."""

    def test_validates_allowed_command(self):
        """Should not raise for allowed commands."""
        config = {"dynamic_commands": {"allow": ["git*"]}}

        # Should not raise
        validate_command("git status", config)

    def test_raises_for_disallowed_command(self):
        """Should raise CommandValidationError for disallowed commands."""
        config = {"dynamic_commands": {"deny": ["rm *"]}}

        with pytest.raises(CommandValidationError) as exc_info:
            validate_command("rm -rf /", config)

        assert "rm *" in str(exc_info.value)
