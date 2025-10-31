"""Tests for configuration file loading and merging."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cllm.config import (
    CACHE_DIR,
    ConfigurationError,
    _find_config_files,
    _interpolate_env_vars,
    _load_yaml_file,
    clear_schema_cache,
    get_cache_path,
    get_cllm_base_path,
    get_config_sources,
    is_remote_schema,
    load_config,
    load_json_schema,
    load_remote_schema,
    merge_config_with_args,
    resolve_schema_file_path,
    validate_against_schema,
)


class TestEnvVarInterpolation:
    """Tests for environment variable interpolation."""

    def test_interpolate_string_with_env_var(self):
        """Test interpolating a string with environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = _interpolate_env_vars("${TEST_VAR}")
            assert result == "test_value"

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
            with pytest.raises(
                ConfigurationError, match="must contain a YAML dictionary"
            ):
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
            cllm_config.write_text(
                "model: gpt-3.5-turbo\ntemperature: 0.5\nmax_tokens: 1000\n"
            )

            # Higher precedence: ./Cllmfile.yml (overrides model and temperature)
            cwd_config = Path(tmpdir) / "Cllmfile.yml"
            cwd_config.write_text("model: gpt-4\ntemperature: 0.7\n")

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()
                # gpt-4 and 0.7 from cwd_config override, max_tokens from cllm_config remains
                assert config == {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }

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
                with pytest.raises(
                    ConfigurationError, match="Configuration 'nonexistent' not found"
                ):
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


class TestResolveSchemaFilePath:
    """Tests for schema file path resolution."""

    def test_resolve_absolute_path(self):
        """Test resolving an absolute path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "object"}')
            f.flush()
            temp_path = Path(f.name)

        try:
            resolved = resolve_schema_file_path(str(temp_path))
            assert resolved == temp_path
        finally:
            temp_path.unlink()

    def test_resolve_absolute_path_not_found(self):
        """Test that absolute path raises error if file doesn't exist."""
        with pytest.raises(ConfigurationError, match="Schema file not found"):
            resolve_schema_file_path("/nonexistent/path/schema.json")

    def test_resolve_relative_path_in_cwd(self):
        """Test resolving relative path found in CWD."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "test.json"
            schema_path.write_text('{"type": "object"}')

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                resolved = resolve_schema_file_path("test.json")
                assert resolved == schema_path

    def test_resolve_relative_path_in_cllm_folder(self):
        """Test resolving relative path found in .cllm folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cllm_dir = Path(tmpdir) / ".cllm"
            cllm_dir.mkdir()
            schema_path = cllm_dir / "test.json"
            schema_path.write_text('{"type": "object"}')

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                resolved = resolve_schema_file_path("test.json")
                assert resolved == schema_path

    def test_resolve_relative_path_prefers_cwd(self):
        """Test that CWD is checked before .cllm folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create schema in both CWD and .cllm
            cwd_schema = Path(tmpdir) / "test.json"
            cwd_schema.write_text('{"type": "string"}')

            cllm_dir = Path(tmpdir) / ".cllm"
            cllm_dir.mkdir()
            cllm_schema = cllm_dir / "test.json"
            cllm_schema.write_text('{"type": "object"}')

            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                resolved = resolve_schema_file_path("test.json")
                # Should resolve to CWD version
                assert resolved == cwd_schema

    def test_resolve_relative_path_not_found(self):
        """Test that relative path raises error if not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("cllm.config.Path.cwd", return_value=Path(tmpdir)):
                with pytest.raises(ConfigurationError, match="Schema file not found"):
                    resolve_schema_file_path("nonexistent.json")


class TestLoadJsonSchema:
    """Tests for JSON schema loading."""

    def test_load_schema_from_dict(self):
        """Test loading schema from a dictionary."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = load_json_schema(schema)
        assert result == schema

    def test_load_invalid_schema_dict(self):
        """Test that invalid schema dict raises error."""
        invalid_schema = {"type": "invalid_type"}
        with pytest.raises(ConfigurationError, match="Invalid JSON schema"):
            load_json_schema(invalid_schema)

    def test_load_schema_from_file(self):
        """Test loading schema from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "object", "properties": {"age": {"type": "number"}}}')
            f.flush()
            temp_path = Path(f.name)

        try:
            with patch("cllm.config.resolve_schema_file_path", return_value=temp_path):
                schema = load_json_schema(str(temp_path))
                assert schema["type"] == "object"
                assert schema["properties"]["age"]["type"] == "number"
        finally:
            temp_path.unlink()

    def test_load_schema_from_file_invalid_json(self):
        """Test that invalid JSON in file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "object", invalid json}')
            f.flush()
            temp_path = Path(f.name)

        try:
            with patch("cllm.config.resolve_schema_file_path", return_value=temp_path):
                with pytest.raises(ConfigurationError, match="Invalid JSON"):
                    load_json_schema(str(temp_path))
        finally:
            temp_path.unlink()

    def test_load_schema_from_file_invalid_schema(self):
        """Test that invalid JSON schema in file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "not_a_valid_type"}')
            f.flush()
            temp_path = Path(f.name)

        try:
            with patch("cllm.config.resolve_schema_file_path", return_value=temp_path):
                with pytest.raises(ConfigurationError, match="Invalid JSON schema"):
                    load_json_schema(str(temp_path))
        finally:
            temp_path.unlink()

    def test_load_schema_invalid_type(self):
        """Test that invalid schema source type raises error."""
        with pytest.raises(ConfigurationError, match="Invalid schema source type"):
            load_json_schema(123)  # Integer is not a valid type


class TestValidateAgainstSchema:
    """Tests for JSON schema validation."""

    def test_validate_valid_data(self):
        """Test validating data that conforms to schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }
        data = {"name": "John", "age": 30}

        # Should not raise any exception
        validate_against_schema(data, schema)

    def test_validate_invalid_data_missing_required(self):
        """Test validation fails when required field is missing."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        data = {}  # Missing required 'name' field

        with pytest.raises(ConfigurationError, match="Schema validation failed"):
            validate_against_schema(data, schema)

    def test_validate_invalid_data_wrong_type(self):
        """Test validation fails when data has wrong type."""
        schema = {"type": "object", "properties": {"age": {"type": "number"}}}
        data = {"age": "not a number"}

        with pytest.raises(ConfigurationError, match="Schema validation failed"):
            validate_against_schema(data, schema)

    def test_validate_array_schema(self):
        """Test validating array data against schema."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        data = ["apple", "banana", "cherry"]

        # Should not raise any exception
        validate_against_schema(data, schema)

    def test_validate_nested_schema(self):
        """Test validating nested object against schema."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
            "required": ["person"],
        }
        data = {"person": {"name": "Jane"}}

        # Should not raise any exception
        validate_against_schema(data, schema)


class TestRemoteSchemaDetection:
    """Tests for remote schema URL detection (ADR-0006)."""

    def test_is_remote_schema_https(self):
        """Test detecting HTTPS URLs."""
        assert is_remote_schema("https://example.com/schema.json") is True

    def test_is_remote_schema_http(self):
        """Test detecting HTTP URLs."""
        assert is_remote_schema("http://example.com/schema.json") is True

    def test_is_remote_schema_local_path(self):
        """Test that local paths are not detected as remote."""
        assert is_remote_schema("/path/to/schema.json") is False
        assert is_remote_schema("./schema.json") is False
        assert is_remote_schema("schema.json") is False


class TestCachePathGeneration:
    """Tests for cache path generation."""

    def test_get_cache_path_generates_hash(self):
        """Test that cache path uses SHA-256 hash of URL."""
        url = "https://example.com/schema.json"
        cache_path = get_cache_path(url)

        # Check that it's in the cache directory
        assert cache_path.parent == CACHE_DIR

        # Check that filename is a hash
        assert cache_path.suffix == ".json"
        assert len(cache_path.stem) == 64  # SHA-256 hash length

    def test_get_cache_path_same_url_same_path(self):
        """Test that same URL generates same cache path."""
        url = "https://example.com/schema.json"
        path1 = get_cache_path(url)
        path2 = get_cache_path(url)
        assert path1 == path2

    def test_get_cache_path_different_url_different_path(self):
        """Test that different URLs generate different cache paths."""
        url1 = "https://example.com/schema1.json"
        url2 = "https://example.com/schema2.json"
        path1 = get_cache_path(url1)
        path2 = get_cache_path(url2)
        assert path1 != path2


class TestRemoteSchemaLoading:
    """Tests for remote schema loading with caching (ADR-0006)."""

    @pytest.fixture
    def valid_schema(self):
        """Sample valid JSON schema."""
        return {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }

    @pytest.fixture
    def mock_response(self, valid_schema):
        """Create a mock response object."""
        from unittest.mock import Mock

        response = Mock()
        response.content = (
            b'{"type": "object", "properties": {"name": {"type": "string"}}}'
        )
        response.json.return_value = valid_schema
        response.raise_for_status.return_value = None
        return response

    def test_https_only_enforcement(self):
        """Test that HTTP URLs are rejected by default."""
        with pytest.raises(ConfigurationError, match="Insecure schema URL"):
            load_remote_schema("http://example.com/schema.json")

    def test_http_allowed_with_env_var(self, mock_response, valid_schema):
        """Test that HTTP URLs work when CLLM_ALLOW_HTTP_SCHEMAS=1."""
        with patch.dict(os.environ, {"CLLM_ALLOW_HTTP_SCHEMAS": "1"}):
            with patch("cllm.config.requests.get", return_value=mock_response):
                schema = load_remote_schema("http://example.com/schema.json")
                assert schema == valid_schema

    def test_download_and_cache_schema(self, mock_response, valid_schema, tmp_path):
        """Test downloading and caching a remote schema."""
        with patch("cllm.config.CACHE_DIR", tmp_path):
            with patch("cllm.config.requests.get", return_value=mock_response):
                schema = load_remote_schema("https://example.com/schema.json")

                # Check schema is returned correctly
                assert schema == valid_schema

                # Check cache file was created
                cache_path = get_cache_path("https://example.com/schema.json")
                cache_file = tmp_path / cache_path.name
                assert cache_file.exists()

    def test_use_cached_schema(self, valid_schema, tmp_path):
        """Test that cached schema is used when within TTL."""
        # Create a cache file
        cache_path = get_cache_path("https://example.com/schema.json")
        cache_file = tmp_path / cache_path.name
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(cache_file, "w") as f:
            json.dump(valid_schema, f)

        # Should use cache without making HTTP request
        with patch("cllm.config.CACHE_DIR", tmp_path):
            with patch("cllm.config.requests.get") as mock_get:
                schema = load_remote_schema("https://example.com/schema.json")

                # Check schema was loaded from cache
                assert schema == valid_schema
                # Check no HTTP request was made
                mock_get.assert_not_called()

    def test_expired_cache_redownloads(self, mock_response, valid_schema, tmp_path):
        """Test that expired cache triggers re-download."""
        # Create an old cache file
        cache_path = get_cache_path("https://example.com/schema.json")
        cache_file = tmp_path / cache_path.name
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(cache_file, "w") as f:
            json.dump(valid_schema, f)

        # Set modification time to 2 days ago
        import time

        old_time = time.time() - (2 * 86400)
        os.utime(cache_file, (old_time, old_time))

        # Should re-download
        with patch("cllm.config.CACHE_DIR", tmp_path):
            with patch(
                "cllm.config.requests.get", return_value=mock_response
            ) as mock_get:
                load_remote_schema("https://example.com/schema.json")

                # Check HTTP request was made
                mock_get.assert_called_once()

    def test_network_error_uses_stale_cache(self, valid_schema, tmp_path):
        """Test that network errors fall back to stale cache."""
        # Create a stale cache file
        cache_path = get_cache_path("https://example.com/schema.json")
        cache_file = tmp_path / cache_path.name
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(cache_file, "w") as f:
            json.dump(valid_schema, f)

        # Simulate network error
        import requests

        with patch("cllm.config.CACHE_DIR", tmp_path):
            with patch(
                "cllm.config.requests.get",
                side_effect=requests.RequestException("Network error"),
            ):
                # Should use stale cache and print warning
                schema = load_remote_schema("https://example.com/schema.json")
                assert schema == valid_schema

    def test_network_error_no_cache_raises(self):
        """Test that network error without cache raises error."""
        import requests

        with patch(
            "cllm.config.requests.get",
            side_effect=requests.RequestException("Network error"),
        ):
            with pytest.raises(ConfigurationError, match="Failed to download schema"):
                load_remote_schema("https://example.com/schema.json")

    def test_timeout_uses_stale_cache(self, valid_schema, tmp_path):
        """Test that timeout falls back to stale cache."""
        # Create a stale cache file
        cache_path = get_cache_path("https://example.com/schema.json")
        cache_file = tmp_path / cache_path.name
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(cache_file, "w") as f:
            json.dump(valid_schema, f)

        # Simulate timeout
        import requests

        with patch("cllm.config.CACHE_DIR", tmp_path):
            with patch(
                "cllm.config.requests.get",
                side_effect=requests.Timeout("Request timeout"),
            ):
                schema = load_remote_schema("https://example.com/schema.json")
                assert schema == valid_schema

    def test_size_limit_enforcement(self, valid_schema):
        """Test that schemas larger than limit are rejected."""
        from unittest.mock import Mock

        response = Mock()
        # Create content larger than 1MB
        response.content = b"x" * (1024 * 1024 + 1)
        response.json.return_value = valid_schema

        with patch("cllm.config.requests.get", return_value=response):
            with pytest.raises(ConfigurationError, match="Schema too large"):
                load_remote_schema("https://example.com/schema.json")

    def test_invalid_json_schema_rejected(self):
        """Test that invalid JSON schemas are rejected."""
        from unittest.mock import Mock

        response = Mock()
        response.content = b'{"type": "invalid_type"}'
        response.json.return_value = {"type": "invalid_type"}

        with patch("cllm.config.requests.get", return_value=response):
            with pytest.raises(ConfigurationError, match="Invalid JSON Schema"):
                load_remote_schema("https://example.com/schema.json")

    def test_invalid_json_rejected(self):
        """Test that invalid JSON is rejected."""
        import json as json_module
        from unittest.mock import Mock

        response = Mock()
        response.content = b"invalid json"
        response.json.side_effect = json_module.JSONDecodeError("error", "doc", 0)

        with patch("cllm.config.requests.get", return_value=response):
            with pytest.raises(ConfigurationError, match="Invalid JSON"):
                load_remote_schema("https://example.com/schema.json")

    def test_offline_mode_uses_cache(self, valid_schema, tmp_path):
        """Test that offline mode uses cache only."""
        # Create a cache file
        cache_path = get_cache_path("https://example.com/schema.json")
        cache_file = tmp_path / cache_path.name
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(cache_file, "w") as f:
            json.dump(valid_schema, f)

        # Test offline mode
        with patch.dict(os.environ, {"CLLM_OFFLINE_MODE": "1"}):
            with patch("cllm.config.CACHE_DIR", tmp_path):
                with patch("cllm.config.requests.get") as mock_get:
                    schema = load_remote_schema("https://example.com/schema.json")

                    # Check schema was loaded from cache
                    assert schema == valid_schema
                    # Check no HTTP request was made
                    mock_get.assert_not_called()

    def test_offline_mode_no_cache_raises(self):
        """Test that offline mode without cache raises error."""
        with patch.dict(os.environ, {"CLLM_OFFLINE_MODE": "1"}):
            with pytest.raises(
                ConfigurationError, match="Cannot download schema in offline mode"
            ):
                load_remote_schema("https://example.com/schema.json")


class TestCacheManagement:
    """Tests for cache management functions."""

    def test_clear_empty_cache(self, tmp_path):
        """Test clearing cache when no cache exists."""
        # Use a temporary directory to ensure it's empty
        empty_cache_dir = tmp_path / "empty_cache"
        empty_cache_dir.mkdir()

        with patch("cllm.config.CACHE_DIR", empty_cache_dir):
            count = clear_schema_cache()
            assert count == 0

    def test_clear_cache_with_files(self, tmp_path):
        """Test clearing cache with cached files."""
        # Create some cache files
        cache_files = []
        for i in range(3):
            cache_file = tmp_path / f"schema{i}.json"
            cache_file.write_text('{"type": "object"}')
            cache_files.append(cache_file)

        with patch("cllm.config.CACHE_DIR", tmp_path):
            count = clear_schema_cache()
            assert count == 3

            # Verify files are deleted
            for cache_file in cache_files:
                assert not cache_file.exists()


class TestLoadJsonSchemaWithUrls:
    """Tests for load_json_schema with URL support."""

    def test_load_schema_from_url(self, tmp_path):
        """Test loading schema from remote URL."""
        valid_schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        from unittest.mock import Mock

        response = Mock()
        response.content = b'{"type": "object"}'
        response.json.return_value = valid_schema

        with patch("cllm.config.CACHE_DIR", tmp_path):
            with patch("cllm.config.requests.get", return_value=response):
                schema = load_json_schema("https://example.com/schema.json")
                assert schema == valid_schema


class TestCustomCllmPath:
    """Tests for ADR-0016: Configurable .cllm Directory Path."""

    def test_get_cllm_base_path_with_cli_flag(self, tmp_path):
        """Test that CLI flag path is returned when provided."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        result = get_cllm_base_path(str(custom_dir))
        assert result == custom_dir

    def test_get_cllm_base_path_with_env_var(self, tmp_path):
        """Test that CLLM_PATH env var is used when CLI flag not provided."""
        custom_dir = tmp_path / "env-cllm"
        custom_dir.mkdir()

        with patch.dict(os.environ, {"CLLM_PATH": str(custom_dir)}):
            result = get_cllm_base_path(cllm_path=None)
            assert result == custom_dir

    def test_get_cllm_base_path_cli_overrides_env(self, tmp_path):
        """Test that CLI flag takes precedence over CLLM_PATH env var."""
        cli_dir = tmp_path / "cli-cllm"
        env_dir = tmp_path / "env-cllm"
        cli_dir.mkdir()
        env_dir.mkdir()

        with patch.dict(os.environ, {"CLLM_PATH": str(env_dir)}):
            result = get_cllm_base_path(str(cli_dir))
            assert result == cli_dir

    def test_get_cllm_base_path_no_override_returns_none(self):
        """Test that None is returned when no custom path is specified."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_cllm_base_path(cllm_path=None)
            assert result is None

    def test_get_cllm_base_path_nonexistent_cli_path_raises_error(self, tmp_path):
        """Test that nonexistent CLI path raises ConfigurationError."""
        nonexistent = tmp_path / "does-not-exist"

        with pytest.raises(ConfigurationError, match="does not exist"):
            get_cllm_base_path(str(nonexistent))

    def test_get_cllm_base_path_nonexistent_env_path_raises_error(self, tmp_path):
        """Test that nonexistent CLLM_PATH raises ConfigurationError."""
        nonexistent = tmp_path / "does-not-exist"

        with patch.dict(os.environ, {"CLLM_PATH": str(nonexistent)}):
            with pytest.raises(
                ConfigurationError, match="CLLM_PATH directory does not exist"
            ):
                get_cllm_base_path(cllm_path=None)

    def test_get_cllm_base_path_file_instead_of_dir_raises_error(self, tmp_path):
        """Test that path pointing to file (not directory) raises error."""
        file_path = tmp_path / "config.yml"
        file_path.write_text("test: value")

        with pytest.raises(ConfigurationError, match="not a directory"):
            get_cllm_base_path(str(file_path))

    def test_find_config_files_with_custom_path(self, tmp_path):
        """Test that _find_config_files uses custom path when provided."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        # Create a config file in custom directory
        config_file = custom_dir / "Cllmfile.yml"
        config_file.write_text("model: gpt-4\n")

        # Find config files with custom path
        result = _find_config_files(config_name=None, cllm_path=str(custom_dir))

        assert len(result) == 1
        assert result[0] == config_file

    def test_find_config_files_custom_path_only_searches_that_dir(self, tmp_path):
        """Test that custom path doesn't fall back to default search."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        # Create config in home directory (should be ignored)
        home_cllm = tmp_path / "home-cllm"
        home_cllm.mkdir()
        home_config = home_cllm / "Cllmfile.yml"
        home_config.write_text("model: gpt-3.5-turbo\n")

        # Custom dir has no config file
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = _find_config_files(config_name=None, cllm_path=str(custom_dir))

            # Should not find anything (doesn't search home directory)
            assert len(result) == 0

    def test_load_config_with_custom_path(self, tmp_path):
        """Test loading config from custom path."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        config_file = custom_dir / "Cllmfile.yml"
        config_file.write_text("model: custom-model\ntemperature: 0.9\n")

        config = load_config(config_name=None, cllm_path=str(custom_dir))

        assert config["model"] == "custom-model"
        assert config["temperature"] == 0.9

    def test_load_named_config_with_custom_path(self, tmp_path):
        """Test loading named config from custom path."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        config_file = custom_dir / "myconfig.Cllmfile.yml"
        config_file.write_text("model: named-model\n")

        config = load_config(config_name="myconfig", cllm_path=str(custom_dir))

        assert config["model"] == "named-model"

    def test_load_config_custom_path_not_found_raises_error(self, tmp_path):
        """Test that missing config in custom path raises error with helpful message."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        # No config file created
        with pytest.raises(ConfigurationError, match="not found in custom path"):
            load_config(config_name="missing", cllm_path=str(custom_dir))

    def test_get_config_sources_with_custom_path(self, tmp_path):
        """Test that get_config_sources respects custom path."""
        custom_dir = tmp_path / "custom-cllm"
        custom_dir.mkdir()

        config_file = custom_dir / "Cllmfile.yml"
        config_file.write_text("model: gpt-4\n")

        sources = get_config_sources(config_name=None, cllm_path=str(custom_dir))

        assert len(sources) == 1
        assert str(custom_dir / "Cllmfile.yml") in sources[0]
