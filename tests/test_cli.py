"""
Tests for the CLI.

These tests verify that the command-line interface works correctly.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cllm.cli import configure_debugging, main, print_model_list


class TestListModels:
    """Test suite for model listing functionality."""

    @patch(
        "cllm.cli.litellm.model_list", ["gpt-4", "claude-3-opus-20240229", "gemini-pro"]
    )
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

    @patch(
        "cllm.cli.litellm.model_list",
        [
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "gemini-pro",
            "gemini-1.5-flash",
        ],
    )
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


class TestValidateSchema:
    """Test suite for --validate-schema flag."""

    @patch(
        "sys.argv",
        [
            "cllm",
            "--validate-schema",
            "--json-schema",
            '{"type": "object", "properties": {"name": {"type": "string"}}}',
        ],
    )
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

    @patch(
        "sys.argv",
        [
            "cllm",
            "--validate-schema",
            "--json-schema",
            '{"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "number"}}, "required": ["name"]}',
        ],
    )
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

    @patch(
        "sys.argv",
        ["cllm", "--validate-schema", "--json-schema", '{"type": "invalid"}'],
    )
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
    @patch(
        "cllm.cli.load_config",
        return_value={
            "json_schema": {
                "type": "object",
                "properties": {"test": {"type": "string"}},
            }
        },
    )
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


class TestDebugging:
    """Test suite for debugging and logging features (ADR-0009)."""

    @patch("cllm.cli.litellm")
    def test_configure_debugging_with_debug_flag(self, mock_litellm, capsys):
        """Test that debug=True sets litellm.set_verbose=True."""
        configure_debugging(debug=True)

        # Verify litellm.set_verbose was set to True
        assert mock_litellm.set_verbose is True

        # Verify warning message is printed
        captured = capsys.readouterr()
        assert "⚠️  Debug mode enabled" in captured.err
        assert "API keys and sensitive data" in captured.err

    @patch("cllm.cli.litellm")
    def test_configure_debugging_with_json_logs(self, mock_litellm):
        """Test that json_logs=True sets litellm.json_logs=True."""
        configure_debugging(json_logs=True)

        # Verify litellm.json_logs was set to True
        assert mock_litellm.json_logs is True

    @patch("cllm.cli.litellm")
    def test_configure_debugging_without_flags(self, mock_litellm):
        """Test that configure_debugging with no flags does nothing."""
        # Reset mock attributes
        mock_litellm.set_verbose = False
        mock_litellm.json_logs = False

        configure_debugging()

        # Verify flags remain False
        assert mock_litellm.set_verbose is False
        assert mock_litellm.json_logs is False

    @patch("cllm.cli.litellm")
    def test_configure_debugging_with_log_file(self, mock_litellm):
        """Test that log_file creates file with proper permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            # Configure with log file
            handle = configure_debugging(log_file=str(log_file))

            # Verify file was created
            assert log_file.exists()

            # Verify file has restrictive permissions (0600) on Unix
            if hasattr(os, "chmod"):
                stat_result = log_file.stat()
                # Check that permissions are 0600 (owner read/write only)
                assert oct(stat_result.st_mode)[-3:] == "600"

            # Clean up
            if handle:
                handle.close()

    @patch("cllm.cli.litellm")
    def test_configure_debugging_log_file_creates_parent_dirs(self, mock_litellm):
        """Test that log_file creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "nested" / "dir" / "test.log"

            # Configure with nested log file path
            handle = configure_debugging(log_file=str(log_file))

            # Verify parent directories were created
            assert log_file.parent.exists()
            assert log_file.exists()

            # Clean up
            if handle:
                handle.close()

    @patch("cllm.cli.litellm")
    def test_configure_debugging_combined_flags(self, mock_litellm, capsys):
        """Test that all debug flags can be combined."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            handle = configure_debugging(
                debug=True, json_logs=True, log_file=str(log_file)
            )

            # Verify all flags were set
            assert mock_litellm.set_verbose is True
            assert mock_litellm.json_logs is True
            assert log_file.exists()

            # Clean up
            if handle:
                handle.close()

    @patch("sys.argv", ["cllm", "--debug", "test prompt"])
    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    @patch("cllm.cli.litellm")
    def test_cli_debug_flag(self, mock_litellm, mock_load_config, mock_client, mock_isatty, capsys):
        """Test that --debug flag enables debug mode via CLI."""
        # Mock the client to avoid actual API calls
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "test response"
        mock_client.return_value = mock_instance

        try:
            main()
        except SystemExit:
            pass

        # Verify debug mode was enabled
        assert mock_litellm.set_verbose is True

        # Verify warning was shown
        captured = capsys.readouterr()
        assert "⚠️  Debug mode enabled" in captured.err

    @patch("sys.argv", ["cllm", "--json-logs", "test prompt"])
    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    @patch("cllm.cli.litellm")
    def test_cli_json_logs_flag(self, mock_litellm, mock_load_config, mock_client, mock_isatty):
        """Test that --json-logs flag enables JSON logging via CLI."""
        # Mock the client to avoid actual API calls
        mock_instance = MagicMock()
        mock_instance.complete.return_value = "test response"
        mock_client.return_value = mock_instance

        try:
            main()
        except SystemExit:
            pass

        # Verify JSON logs were enabled
        assert mock_litellm.json_logs is True

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    @patch("cllm.cli.litellm")
    def test_cli_log_file_flag(self, mock_litellm, mock_load_config, mock_client, mock_isatty):
        """Test that --log-file flag creates log file via CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "cli-test.log"

            with patch("sys.argv", ["cllm", "--log-file", str(log_file), "test prompt"]):
                # Mock the client to avoid actual API calls
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "test response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify log file was created
                assert log_file.exists()

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    @patch("cllm.cli.litellm")
    def test_debug_from_cllmfile(self, mock_litellm, mock_load_config, mock_client, mock_isatty):
        """Test that debug settings from Cllmfile are applied."""
        # Mock config to include debug settings
        mock_load_config.return_value = {
            "debug": True,
            "json_logs": True,
        }

        with patch("sys.argv", ["cllm", "test prompt"]):
            # Mock the client to avoid actual API calls
            mock_instance = MagicMock()
            mock_instance.complete.return_value = "test response"
            mock_client.return_value = mock_instance

            try:
                main()
            except SystemExit:
                pass

            # Verify debug settings were applied from config
            assert mock_litellm.set_verbose is True
            assert mock_litellm.json_logs is True

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={"debug": False})
    @patch("cllm.cli.litellm")
    def test_cli_flag_overrides_cllmfile(self, mock_litellm, mock_load_config, mock_client, mock_isatty):
        """Test that CLI flag overrides Cllmfile setting."""
        with patch("sys.argv", ["cllm", "--debug", "test prompt"]):
            # Mock the client to avoid actual API calls
            mock_instance = MagicMock()
            mock_instance.complete.return_value = "test response"
            mock_client.return_value = mock_instance

            try:
                main()
            except SystemExit:
                pass

            # Verify CLI flag overrode config
            assert mock_litellm.set_verbose is True

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    @patch("cllm.cli.litellm")
    def test_environment_variable_debug(self, mock_litellm, mock_load_config, mock_client, mock_isatty):
        """Test that CLLM_DEBUG environment variable enables debug mode."""
        with patch.dict(os.environ, {"CLLM_DEBUG": "1"}):
            with patch("sys.argv", ["cllm", "test prompt"]):
                # Mock the client to avoid actual API calls
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "test response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify debug mode was enabled via environment variable
                assert mock_litellm.set_verbose is True

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    @patch("cllm.cli.litellm")
    def test_environment_variable_json_logs(self, mock_litellm, mock_load_config, mock_client, mock_isatty):
        """Test that CLLM_JSON_LOGS environment variable enables JSON logging."""
        with patch.dict(os.environ, {"CLLM_JSON_LOGS": "1"}):
            with patch("sys.argv", ["cllm", "test prompt"]):
                # Mock the client to avoid actual API calls
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "test response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify JSON logs were enabled via environment variable
                assert mock_litellm.json_logs is True


class TestContextInjection:
    """Integration tests for context injection (ADR-0011)."""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    def test_exec_flag_single_command(self, mock_load_config, mock_client, mock_isatty):
        """Test --exec flag with single command."""
        with patch("sys.argv", ["cllm", "--exec", "echo 'test context'", "Analyze this"]):
            # Mock the client to capture what prompt was sent
            mock_instance = MagicMock()
            mock_instance.complete.return_value = "response"
            mock_client.return_value = mock_instance

            try:
                main()
            except SystemExit:
                pass

            # Verify complete was called with context-injected prompt
            assert mock_instance.complete.called
            call_args = mock_instance.complete.call_args
            messages = call_args[1]["messages"]

            # The prompt should contain context block
            assert "--- Context: CLI Command 1 ---" in messages
            assert "test context" in messages
            assert "Analyze this" in messages

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    @patch("cllm.cli.load_config", return_value={})
    def test_exec_flag_multiple_commands(self, mock_load_config, mock_client, mock_isatty):
        """Test --exec flag with multiple commands."""
        with patch(
            "sys.argv",
            [
                "cllm",
                "--exec",
                "echo 'first'",
                "--exec",
                "echo 'second'",
                "Analyze",
            ],
        ):
            # Mock the client
            mock_instance = MagicMock()
            mock_instance.complete.return_value = "response"
            mock_client.return_value = mock_instance

            try:
                main()
            except SystemExit:
                pass

            # Verify both context blocks are present
            call_args = mock_instance.complete.call_args
            messages = call_args[1]["messages"]

            assert "--- Context: CLI Command 1 ---" in messages
            assert "first" in messages
            assert "--- Context: CLI Command 2 ---" in messages
            assert "second" in messages
            assert "Analyze" in messages

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    def test_context_commands_from_config(self, mock_client, mock_isatty):
        """Test context_commands from Cllmfile configuration."""
        config = {
            "context_commands": [
                {"name": "Git Status", "command": "echo 'M file.py'"},
                {"name": "Test Output", "command": "echo 'All tests passed'"},
            ]
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "Analyze this"]):
                # Mock the client
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify context blocks from config
                call_args = mock_instance.complete.call_args
                messages = call_args[1]["messages"]

                assert "--- Context: Git Status ---" in messages
                assert "M file.py" in messages
                assert "--- Context: Test Output ---" in messages
                assert "All tests passed" in messages

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    def test_no_context_exec_flag(self, mock_client, mock_isatty):
        """Test --no-context-exec disables config commands."""
        config = {
            "context_commands": [
                {"name": "Should Be Skipped", "command": "echo 'skipped'"}
            ]
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "--no-context-exec", "Prompt"]):
                # Mock the client
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify context was NOT injected
                call_args = mock_instance.complete.call_args
                messages = call_args[1]["messages"]

                assert "Should Be Skipped" not in messages
                assert "skipped" not in messages
                assert messages == "Prompt"  # Original prompt unchanged

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    def test_config_and_cli_commands_precedence(self, mock_client, mock_isatty):
        """Test that config commands run first, then CLI commands."""
        config = {
            "context_commands": [{"name": "Config Cmd", "command": "echo 'from config'"}]
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "--exec", "echo 'from cli'", "Prompt"]):
                # Mock the client
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify both are present
                call_args = mock_instance.complete.call_args
                messages = call_args[1]["messages"]

                assert "--- Context: Config Cmd ---" in messages
                assert "from config" in messages
                assert "--- Context: CLI Command 1 ---" in messages
                assert "from cli" in messages

                # Verify order: config command appears before CLI command
                config_idx = messages.index("Config Cmd")
                cli_idx = messages.index("CLI Command 1")
                assert config_idx < cli_idx

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    def test_command_failure_with_warn(self, mock_client, mock_isatty):
        """Test that failing command with on_failure=warn includes error."""
        config = {
            "context_commands": [
                {
                    "name": "Failing Cmd",
                    "command": "exit 1",
                    "on_failure": "warn",
                }
            ]
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "Prompt"]):
                # Mock the client
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify error block is included
                call_args = mock_instance.complete.call_args
                messages = call_args[1]["messages"]

                assert "--- Context Error: Failing Cmd ---" in messages
                assert "exited with code 1" in messages

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    def test_command_failure_with_ignore(self, mock_client, mock_isatty):
        """Test that failing command with on_failure=ignore is skipped."""
        config = {
            "context_commands": [
                {
                    "name": "Failing Cmd",
                    "command": "exit 1",
                    "on_failure": "ignore",
                }
            ]
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "Prompt"]):
                # Mock the client
                mock_instance = MagicMock()
                mock_instance.complete.return_value = "response"
                mock_client.return_value = mock_instance

                try:
                    main()
                except SystemExit:
                    pass

                # Verify error block is NOT included
                call_args = mock_instance.complete.call_args
                messages = call_args[1]["messages"]

                assert "Failing Cmd" not in messages
                assert messages == "Prompt"  # Original prompt unchanged

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.LLMClient")
    def test_command_failure_with_fail(self, mock_client, mock_isatty, capsys):
        """Test that failing command with on_failure=fail aborts."""
        config = {
            "context_commands": [
                {
                    "name": "Failing Cmd",
                    "command": "exit 1",
                    "on_failure": "fail",
                }
            ]
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "Prompt"]):
                # Mock the client (should not be called)
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with error code
                assert exc_info.value.code == 1

                # Verify error message was printed
                captured = capsys.readouterr()
                assert "Context error:" in captured.err
                assert "Failing Cmd" in captured.err

                # Verify LLM was NOT called
                assert not mock_instance.complete.called


class TestDynamicCommandsWithJsonSchema:
    """Integration tests for --allow-commands with --json-schema (ADR-0014)."""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.execute_with_dynamic_commands")
    @patch("cllm.cli.load_config", return_value={})
    def test_allow_commands_with_json_schema(
        self, mock_load_config, mock_execute, mock_isatty, capsys
    ):
        """Test that --allow-commands works with --json-schema."""
        schema = '{"type": "object", "properties": {"result": {"type": "string"}}}'

        with patch(
            "sys.argv",
            ["cllm", "--allow-commands", "--json-schema", schema, "test prompt"],
        ):
            # Mock execute_with_dynamic_commands to return JSON
            mock_execute.return_value = '{"result": "test output"}'

            try:
                main()
            except SystemExit:
                pass

            # Verify execute_with_dynamic_commands was called with schema
            assert mock_execute.called
            call_kwargs = mock_execute.call_args[1]
            assert "schema" in call_kwargs
            assert call_kwargs["schema"]["type"] == "object"
            assert "result" in call_kwargs["schema"]["properties"]

            # Verify no warning about unsupported feature
            captured = capsys.readouterr()
            assert "not yet supported" not in captured.err
            assert "not supported" not in captured.err or "Streaming is not supported" in captured.err

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.execute_with_dynamic_commands")
    @patch("cllm.cli.load_config", return_value={})
    def test_allow_commands_with_json_schema_file(
        self, mock_load_config, mock_execute, mock_isatty
    ):
        """Test that --allow-commands works with --json-schema-file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            schema = {
                "type": "object",
                "properties": {"answer": {"type": "number"}},
                "required": ["answer"],
            }
            import json

            json.dump(schema, f)
            schema_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "cllm",
                    "--allow-commands",
                    "--json-schema-file",
                    schema_file,
                    "calculate",
                ],
            ):
                # Mock execute_with_dynamic_commands to return JSON
                mock_execute.return_value = '{"answer": 42}'

                try:
                    main()
                except SystemExit:
                    pass

                # Verify execute_with_dynamic_commands was called with schema
                assert mock_execute.called
                call_kwargs = mock_execute.call_args[1]
                assert "schema" in call_kwargs
                assert call_kwargs["schema"]["type"] == "object"
                assert "answer" in call_kwargs["schema"]["properties"]
                assert call_kwargs["schema"]["required"] == ["answer"]
        finally:
            # Clean up temp file
            os.unlink(schema_file)

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.execute_with_dynamic_commands")
    def test_allow_commands_with_json_schema_from_config(
        self, mock_execute, mock_isatty
    ):
        """Test that --allow-commands works with JSON schema from Cllmfile."""
        config = {
            "allow_dynamic_commands": True,
            "json_schema": {
                "type": "object",
                "properties": {"status": {"type": "string"}},
            },
        }

        with patch("cllm.cli.load_config", return_value=config):
            with patch("sys.argv", ["cllm", "check status"]):
                # Mock execute_with_dynamic_commands to return JSON
                mock_execute.return_value = '{"status": "ok"}'

                try:
                    main()
                except SystemExit:
                    pass

                # Verify execute_with_dynamic_commands was called with schema
                assert mock_execute.called
                call_kwargs = mock_execute.call_args[1]
                assert "schema" in call_kwargs
                assert call_kwargs["schema"]["type"] == "object"
                assert "status" in call_kwargs["schema"]["properties"]

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.execute_with_dynamic_commands")
    @patch("cllm.cli.load_config", return_value={})
    def test_streaming_warning_with_allow_commands(
        self, mock_load_config, mock_execute, mock_isatty, capsys
    ):
        """Test that streaming shows warning with --allow-commands."""
        with patch("sys.argv", ["cllm", "--allow-commands", "--stream", "test"]):
            mock_execute.return_value = "response"

            try:
                main()
            except SystemExit:
                pass

            # Verify warning is shown
            captured = capsys.readouterr()
            assert "Streaming is not supported with --allow-commands" in captured.err

    @patch("sys.stdin.isatty", return_value=True)
    @patch("cllm.cli.execute_with_dynamic_commands")
    @patch("cllm.cli.load_config", return_value={})
    def test_raw_response_warning_with_allow_commands(
        self, mock_load_config, mock_execute, mock_isatty, capsys
    ):
        """Test that raw response shows warning with --allow-commands."""
        with patch("sys.argv", ["cllm", "--allow-commands", "--raw", "test"]):
            mock_execute.return_value = "response"

            try:
                main()
            except SystemExit:
                pass

            # Verify warning is shown
            captured = capsys.readouterr()
            assert "Raw response is not supported with --allow-commands" in captured.err
