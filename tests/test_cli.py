"""
Tests for the CLI.

These tests verify that the command-line interface works correctly.
"""

import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from cllm.cli import create_parser, main, print_model_list


class TestCLIArguments:
    """Test suite for CLI argument parsing."""

    def test_list_models_flag_exists(self):
        """Test that --list-models flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["--list-models"])
        assert args.list_models is True

    def test_list_models_flag_default(self):
        """Test that --list-models defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["test prompt"])
        assert args.list_models is False


class TestListModels:
    """Test suite for model listing functionality."""

    @patch("cllm.cli.litellm.model_list", ["gpt-4", "claude-3-opus-20240229", "gemini-pro"])
    def test_print_model_list_output(self, capsys):
        """Test that print_model_list produces expected output."""
        print_model_list()
        captured = capsys.readouterr()

        # Verify header is present
        assert "Available Models" in captured.out
        assert "3 total" in captured.out

        # Verify models are listed
        assert "gpt-4" in captured.out
        assert "claude-3-opus-20240229" in captured.out
        assert "gemini-pro" in captured.out

        # Verify tip is shown
        assert "grep" in captured.out

    @patch("cllm.cli.litellm.model_list", [
        "gpt-4",
        "gpt-3.5-turbo",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "gemini-pro",
        "gemini-1.5-flash",
    ])
    def test_print_model_list_categorization(self, capsys):
        """Test that models are categorized by provider."""
        print_model_list()
        captured = capsys.readouterr()

        # Verify provider headers are present
        assert "OpenAI:" in captured.out
        assert "Anthropic:" in captured.out
        assert "Google:" in captured.out

    @patch("cllm.cli.litellm.model_list", [])
    def test_print_model_list_empty(self, capsys):
        """Test print_model_list with empty model list."""
        print_model_list()
        captured = capsys.readouterr()

        # Should still print header with 0 total
        assert "Available Models" in captured.out
        assert "0 total" in captured.out


class TestListModelsIntegration:
    """Integration tests for --list-models flag."""

    @patch("cllm.cli.litellm.model_list", ["gpt-4", "claude-3-opus-20240229"])
    @patch("sys.argv", ["cllm", "--list-models"])
    def test_list_models_exits_successfully(self, capsys):
        """Test that --list-models exits after printing."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 0
        assert exc_info.value.code == 0

        # Should have printed models
        captured = capsys.readouterr()
        assert "Available Models" in captured.out
        assert "gpt-4" in captured.out
        assert "claude-3-opus-20240229" in captured.out

    @patch("cllm.cli.litellm.model_list", ["gpt-4"])
    @patch("sys.argv", ["cllm", "--list-models"])
    @patch("cllm.cli.read_prompt")
    def test_list_models_does_not_read_prompt(self, mock_read_prompt, capsys):
        """Test that --list-models doesn't try to read prompt."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit successfully
        assert exc_info.value.code == 0

        # Should NOT have called read_prompt
        mock_read_prompt.assert_not_called()

    @patch("cllm.cli.litellm.model_list", ["gpt-4"])
    @patch("sys.argv", ["cllm", "--list-models", "--model", "gpt-4"])
    @patch("cllm.cli.LLMClient")
    def test_list_models_does_not_create_client(self, mock_client, capsys):
        """Test that --list-models doesn't initialize LLMClient."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit successfully
        assert exc_info.value.code == 0

        # Should NOT have created client
        mock_client.assert_not_called()


class TestListModelsGrep:
    """Test that --list-models output is grep-friendly."""

    @patch("cllm.cli.litellm.model_list", [
        "gpt-4",
        "gpt-3.5-turbo",
        "claude-3-opus-20240229",
        "gemini-pro",
    ])
    def test_models_on_separate_lines(self, capsys):
        """Test that each model appears on its own line for grep-ability."""
        print_model_list()
        captured = capsys.readouterr()

        # Each model should be on its own line
        lines = captured.out.split('\n')
        model_lines = [line.strip() for line in lines if line.strip() and not line.startswith('=')]

        # Find lines that contain our models
        gpt4_lines = [line for line in model_lines if 'gpt-4' in line and 'gpt-3.5' not in line]
        gpt35_lines = [line for line in model_lines if 'gpt-3.5-turbo' in line]
        claude_lines = [line for line in model_lines if 'claude-3-opus-20240229' in line]
        gemini_lines = [line for line in model_lines if 'gemini-pro' in line]

        # Each model should appear at least once
        assert len(gpt4_lines) >= 1
        assert len(gpt35_lines) >= 1
        assert len(claude_lines) >= 1
        assert len(gemini_lines) >= 1


class TestValidateSchema:
    """Test suite for --validate-schema flag."""

    def test_validate_schema_flag_exists(self):
        """Test that --validate-schema flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["--validate-schema"])
        assert args.validate_schema is True

    def test_validate_schema_flag_default(self):
        """Test that --validate-schema defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["test prompt"])
        assert args.validate_schema is False

    @patch("sys.argv", ["cllm", "--validate-schema", "--json-schema", '{"type": "object", "properties": {"name": {"type": "string"}}}'])
    @patch("cllm.cli.load_config", return_value={})
    def test_validate_schema_with_inline_json(self, mock_load_config, capsys):
        """Test --validate-schema with inline JSON schema."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

        # Should print validation success
        captured = capsys.readouterr()
        assert "Schema is valid" in captured.out
        assert "Schema validation successful" in captured.out

    @patch("sys.argv", ["cllm", "--validate-schema", "--json-schema", '{"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "number"}}, "required": ["name"]}'])
    @patch("cllm.cli.load_config", return_value={})
    def test_validate_schema_shows_object_details(self, mock_load_config, capsys):
        """Test that --validate-schema shows details about object schemas."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Type: object" in captured.out
        assert "Properties: 2" in captured.out
        assert "name: string (required)" in captured.out
        assert "age: number (optional)" in captured.out

    @patch("sys.argv", ["cllm", "--validate-schema", "--json-schema", '{"type": "array", "items": {"type": "string"}}'])
    @patch("cllm.cli.load_config", return_value={})
    def test_validate_schema_shows_array_details(self, mock_load_config, capsys):
        """Test that --validate-schema shows details about array schemas."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Type: array" in captured.out
        assert "Items type: string" in captured.out

    @patch("sys.argv", ["cllm", "--validate-schema"])
    @patch("cllm.cli.load_config", return_value={})
    def test_validate_schema_without_schema_errors(self, mock_load_config, capsys):
        """Test that --validate-schema without a schema shows error."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 1 (error)
        assert exc_info.value.code == 1

        # Should print error message
        captured = capsys.readouterr()
        assert "Error: No schema provided" in captured.err
        assert "--json-schema or --json-schema-file" in captured.err

    @patch("sys.argv", ["cllm", "--validate-schema", "--json-schema", '{"type": "invalid"}'])
    @patch("cllm.cli.load_config", return_value={})
    def test_validate_schema_with_invalid_schema(self, mock_load_config, capsys):
        """Test that --validate-schema with invalid schema shows error."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 1 (error)
        assert exc_info.value.code == 1

        # Should print schema error
        captured = capsys.readouterr()
        assert "Schema error" in captured.err

    @patch("sys.argv", ["cllm", "--validate-schema"])
    @patch("cllm.cli.load_config", return_value={"json_schema": {"type": "object", "properties": {"test": {"type": "string"}}}})
    def test_validate_schema_from_cllmfile(self, mock_load_config, capsys):
        """Test --validate-schema with schema from Cllmfile."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 0 (success)
        assert exc_info.value.code == 0

        # Should print validation success
        captured = capsys.readouterr()
        assert "Schema is valid" in captured.out
        assert "Type: object" in captured.out

    @patch("sys.argv", ["cllm", "--validate-schema"])
    @patch("cllm.cli.read_prompt")
    @patch("cllm.cli.load_config", return_value={"json_schema": {"type": "object"}})
    def test_validate_schema_does_not_read_prompt(self, mock_load_config, mock_read_prompt, capsys):
        """Test that --validate-schema doesn't try to read prompt."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit successfully
        assert exc_info.value.code == 0

        # Should NOT have called read_prompt
        mock_read_prompt.assert_not_called()

    @patch("sys.argv", ["cllm", "--validate-schema", "--json-schema", '{"type": "object"}'])
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    def test_validate_schema_does_not_create_client(self, mock_load_config, mock_client, capsys):
        """Test that --validate-schema doesn't initialize LLMClient."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit successfully
        assert exc_info.value.code == 0

        # Should NOT have created client
        mock_client.assert_not_called()
