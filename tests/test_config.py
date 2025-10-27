"""Tests for configuration file loading and merging."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cllm.config import (
    ConfigurationError,
    _find_config_files,
    _interpolate_env_vars,
    _load_yaml_file,
    get_config_sources,
    load_config,
    merge_config_with_args,
)


class TestEnvVarInterpolation:
    """Tests for environment variable interpolation."""

    def test_interpolate_string_with_env_var(self):
        """Test interpolating a string with environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = _interpolate_env_vars("${TEST_VAR}")
            assert result == "test_value"

    def test_interpolate_string_with_multiple_env_vars(self):
        """Test interpolating multiple environment variables in one string."""
        with patch.dict(os.environ, {"VAR1": "hello", "VAR2": "world"}):
            result = _interpolate_env_vars("${VAR1} ${VAR2}")
            assert result == "hello world"

    def test_interpolate_missing_env_var(self):
        """Test that missing env vars are left as-is."""
        result = _interpolate_env_vars("${NONEXISTENT_VAR}")
        assert result == "${NONEXISTENT_VAR}"

    def test_interpolate_dict(self):
        """Test interpolating environment variables in a dictionary."""
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            config = {"api_key": "${API_KEY}", "model": "gpt-4"}
            result = _interpolate_env_vars(config)
            assert result == {"api_key": "secret123", "model": "gpt-4"}

    def test_interpolate_list(self):
        """Test interpolating environment variables in a list."""
        with patch.dict(os.environ, {"MODEL": "gpt-4"}):
            config = ["${MODEL}", "claude-3"]
            result = _interpolate_env_vars(config)
            assert result == ["gpt-4", "claude-3"]

    def test_interpolate_nested_structure(self):
        """Test interpolating nested dictionaries and lists."""
        with patch.dict(os.environ, {"HOST": "localhost", "PORT": "6379"}):
            config = {
                "cache": {"redis": {"host": "${HOST}", "port": "${PORT}"}},
                "fallbacks": ["${MODEL}"],
            }
            result = _interpolate_env_vars(config)
            assert result["cache"]["redis"]["host"] == "localhost"
            assert result["cache"]["redis"]["port"] == "6379"


class TestLoadYamlFile:
    """Tests for YAML file loading."""

    def test_load_valid_yaml(self):
        """Test loading a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("model: gpt-4\ntemperature: 0.7\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            config = _load_yaml_file(temp_path)
            assert config == {"model": "gpt-4", "temperature": 0.7}
        finally:
            temp_path.unlink()

    def test_load_empty_yaml(self):
        """Test loading an empty YAML file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")
            f.flush()
            temp_path = Path(f.name)

        try:
            config = _load_yaml_file(temp_path)
            assert config == {}
        finally:
            temp_path.unlink()

    def test_load_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: [\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match="Error parsing YAML"):
                _load_yaml_file(temp_path)
        finally:
            temp_path.unlink()

    def test_load_non_dict_yaml_raises_error(self):
        """Test that YAML containing non-dict raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("- item1\n- item2\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match="must contain a YAML dictionary"):
                _load_yaml_file(temp_path)
        finally:
            temp_path.unlink()

    def test_load_with_env_var_interpolation(self):
        """Test that environment variables are interpolated when loading."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("api_key: ${TEST_API_KEY}\nmodel: gpt-4\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"TEST_API_KEY": "sk-12345"}):
                config = _load_yaml_file(temp_path)
                assert config == {"api_key": "sk-12345", "model": "gpt-4"}
        finally:
            temp_path.unlink()


class TestFindConfigFiles:
    """Tests for configuration file discovery."""

    def test_find_default_config_in_cwd(self):
        """Test finding Cllmfile.yml in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "Cllmfile.yml"
            config_path.write_text("model: gpt-4\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                files = _find_config_files()
                assert len(files) == 1
                assert files[0] == config_path

    def test_find_config_in_cllm_folder(self):
        """Test finding Cllmfile.yml in .cllm folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cllm_dir = Path(tmpdir) / ".cllm"
            cllm_dir.mkdir()
            config_path = cllm_dir / "Cllmfile.yml"
            config_path.write_text("model: gpt-4\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                files = _find_config_files()
                assert len(files) == 1
                assert files[0] == config_path

    def test_find_named_config(self):
        """Test finding named configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "summarize.Cllmfile.yml"
            config_path.write_text("model: claude-3\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                files = _find_config_files(config_name="summarize")
                assert len(files) == 1
                assert files[0] == config_path

    def test_precedence_order(self):
        """Test that files are returned in correct precedence order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config in current directory
            cwd_config = Path(tmpdir) / "Cllmfile.yml"
            cwd_config.write_text("model: gpt-4\n")

            # Create config in .cllm folder
            cllm_dir = Path(tmpdir) / ".cllm"
            cllm_dir.mkdir()
            cllm_config = cllm_dir / "Cllmfile.yml"
            cllm_config.write_text("model: gpt-3.5-turbo\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                files = _find_config_files()
                # Should return in order: .cllm, then cwd (lowest to highest precedence)
                assert len(files) == 2
                assert files[0] == cllm_config
                assert files[1] == cwd_config

    def test_no_config_files_found(self):
        """Test when no configuration files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                files = _find_config_files()
                assert files == []


class TestLoadConfig:
    """Tests for configuration loading and merging."""

    def test_load_single_config(self):
        """Test loading a single configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "Cllmfile.yml"
            config_path.write_text("model: gpt-4\ntemperature: 0.7\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()
                assert config == {"model": "gpt-4", "temperature": 0.7}

    def test_load_and_merge_multiple_configs(self):
        """Test that multiple configs are merged with correct precedence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Lower precedence: .cllm/Cllmfile.yml
            cllm_dir = Path(tmpdir) / ".cllm"
            cllm_dir.mkdir()
            cllm_config = cllm_dir / "Cllmfile.yml"
            cllm_config.write_text("model: gpt-3.5-turbo\ntemperature: 0.5\nmax_tokens: 1000\n")

            # Higher precedence: ./Cllmfile.yml (overrides model and temperature)
            cwd_config = Path(tmpdir) / "Cllmfile.yml"
            cwd_config.write_text("model: gpt-4\ntemperature: 0.7\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()
                # gpt-4 and 0.7 from cwd_config override, max_tokens from cllm_config remains
                assert config == {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}

    def test_load_named_config(self):
        """Test loading a named configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "summarize.Cllmfile.yml"
            config_path.write_text("model: claude-3\nmax_tokens: 500\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config(config_name="summarize")
                assert config == {"model": "claude-3", "max_tokens": 500}

    def test_load_nonexistent_named_config_raises_error(self):
        """Test that requesting a non-existent named config raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                with pytest.raises(ConfigurationError, match="Configuration 'nonexistent' not found"):
                    load_config(config_name="nonexistent")

    def test_load_no_config_returns_empty_dict(self):
        """Test that no config files returns empty dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()
                assert config == {}


class TestMergeConfigWithArgs:
    """Tests for merging configuration with CLI arguments."""

    def test_cli_args_override_config(self):
        """Test that CLI arguments override config file values."""
        config = {"model": "gpt-3.5-turbo", "temperature": 0.5}
        cli_args = {"model": "gpt-4", "temperature": 0.9}
        result = merge_config_with_args(config, cli_args)
        assert result == {"model": "gpt-4", "temperature": 0.9}

    def test_none_cli_args_dont_override(self):
        """Test that None CLI arguments don't override config values."""
        config = {"model": "gpt-4", "temperature": 0.7}
        cli_args = {"model": None, "temperature": 0.9, "max_tokens": None}
        result = merge_config_with_args(config, cli_args)
        assert result == {"model": "gpt-4", "temperature": 0.9}

    def test_cli_args_add_new_keys(self):
        """Test that CLI arguments can add keys not in config."""
        config = {"model": "gpt-4"}
        cli_args = {"temperature": 0.7, "max_tokens": 1000}
        result = merge_config_with_args(config, cli_args)
        assert result == {"model": "gpt-4", "temperature": 0.7, "max_tokens": 1000}

    def test_empty_config_with_cli_args(self):
        """Test merging empty config with CLI arguments."""
        config = {}
        cli_args = {"model": "gpt-4", "temperature": 0.7}
        result = merge_config_with_args(config, cli_args)
        assert result == {"model": "gpt-4", "temperature": 0.7}


class TestGetConfigSources:
    """Tests for getting configuration source paths."""

    def test_get_sources_with_configs(self):
        """Test getting list of config source paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "Cllmfile.yml"
            config_path.write_text("model: gpt-4\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                sources = get_config_sources()
                assert len(sources) == 1
                assert sources[0] == str(config_path)

    def test_get_sources_no_configs(self):
        """Test getting sources when no configs exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                sources = get_config_sources()
                assert sources == []
