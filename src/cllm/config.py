"""Configuration file loading and merging for CLLM.

Implements ADR-0003: Cllmfile Configuration System
Implements ADR-0005: Add Structured Output Support with JSON Schema
Implements ADR-0006: Support Remote JSON Schema URLs
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Match, cast

import jsonschema
import requests
import yaml


class ConfigurationError(Exception):
    """Raised when there's an error loading or parsing configuration files."""

    pass


# Cache configuration for remote schemas (ADR-0006)
CACHE_DIR = Path.home() / ".cllm" / "cache" / "schemas"
DEFAULT_CACHE_TTL = 86400  # 24 hours in seconds
MAX_SCHEMA_SIZE = 1024 * 1024  # 1MB


def _interpolate_env_vars(value: Any) -> Any:
    """Recursively interpolate environment variables in configuration values.

    Supports ${VAR_NAME} syntax. If the environment variable doesn't exist,
    the placeholder is left as-is.

    Args:
        value: Configuration value (can be string, dict, list, or other types)

    Returns:
        Value with environment variables interpolated
    """
    if isinstance(value, str):
        # Match ${VAR_NAME} pattern
        pattern = r"\$\{([^}]+)\}"

        def replacer(match: Match[str]) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replacer, value)
    elif isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    else:
        return value


def _load_yaml_file(file_path: Path) -> dict[str, Any]:
    """Load and parse a YAML configuration file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary of configuration values

    Raises:
        ConfigurationError: If file cannot be read or parsed
    """
    try:
        with open(file_path) as f:
            config = yaml.safe_load(f)
            if config is None:
                return {}
            if not isinstance(config, dict):
                raise ConfigurationError(
                    f"Configuration file {file_path} must contain a YAML dictionary"
                )
            interpolated = _interpolate_env_vars(config)
            if not isinstance(interpolated, dict):
                raise ConfigurationError(
                    f"Configuration file {file_path} must produce a dictionary after interpolation"
                )
            return cast(dict[str, Any], interpolated)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Error parsing YAML file {file_path}: {e}") from e
    except OSError as e:
        raise ConfigurationError(f"Error reading file {file_path}: {e}") from e


def get_cllm_base_path(cllm_path: str | None = None) -> Path | None:
    """Get the effective .cllm base directory path based on precedence.

    Implements ADR-0016: Configurable .cllm Directory Path

    Precedence order:
    1. cllm_path parameter (from --cllm-path CLI flag)
    2. CLLM_PATH environment variable
    3. None (use default search order)

    Args:
        cllm_path: Optional custom path from CLI flag

    Returns:
        Path to custom .cllm directory, or None to use default search order

    Raises:
        ConfigurationError: If custom path is specified but doesn't exist
    """
    # Check CLI flag first
    if cllm_path is not None:
        custom_path = Path(cllm_path)
        if not custom_path.exists():
            raise ConfigurationError(
                f"Custom .cllm path does not exist: {cllm_path}\n"
                f"Suggestion: Create the directory or verify the path is correct"
            )
        if not custom_path.is_dir():
            raise ConfigurationError(
                f"Custom .cllm path is not a directory: {cllm_path}"
            )
        return custom_path

    # Check environment variable
    env_path = os.getenv("CLLM_PATH")
    if env_path:
        custom_path = Path(env_path)
        if not custom_path.exists():
            raise ConfigurationError(
                f"CLLM_PATH directory does not exist: {env_path}\n"
                f"Suggestion: Create the directory, unset CLLM_PATH, or verify the path"
            )
        if not custom_path.is_dir():
            raise ConfigurationError(f"CLLM_PATH is not a directory: {env_path}")
        return custom_path

    # No custom path specified, use default search order
    return None


def _find_config_files(
    config_name: str | None = None, cllm_path: str | None = None
) -> list[Path]:
    """Find all applicable configuration files in order of precedence.

    Implements ADR-0016: Configurable .cllm Directory Path

    If cllm_path is specified (via CLI flag or CLLM_PATH env var), searches only
    in that directory. Otherwise, uses default search order:

    Default search order (lowest to highest precedence):
    1. ~/.cllm/Cllmfile.yml (or ~/.cllm/<name>.Cllmfile.yml)
    2. ./.cllm/Cllmfile.yml (or ./.cllm/<name>.Cllmfile.yml)
    3. ./Cllmfile.yml (or ./<name>.Cllmfile.yml)

    Args:
        config_name: Optional named configuration (e.g., "summarize")
        cllm_path: Optional custom .cllm directory path (from --cllm-path or CLLM_PATH)

    Returns:
        List of existing config file paths, in order from lowest to highest precedence

    Raises:
        ConfigurationError: If custom path is specified but invalid
    """
    if config_name:
        filename = f"{config_name}.Cllmfile.yml"
    else:
        filename = "Cllmfile.yml"

    # Check for custom path override
    base_path = get_cllm_base_path(cllm_path)

    if base_path is not None:
        # Custom path specified - search only in that directory
        search_paths: list[Path] = [base_path / filename]
    else:
        # Default search order
        search_paths = [
            Path.home() / ".cllm" / filename,  # User home
            Path.cwd() / ".cllm" / filename,  # Project .cllm folder
            Path.cwd() / filename,  # Current directory
        ]

    # Return only files that exist, in order
    return [path for path in search_paths if path.exists() and path.is_file()]


def load_config(
    config_name: str | None = None, cllm_path: str | None = None
) -> dict[str, Any]:
    """Load and merge configuration files.

    Implements ADR-0016: Configurable .cllm Directory Path

    Configurations are loaded from multiple locations and merged with later
    files taking precedence. CLI arguments should override these values.

    Args:
        config_name: Optional named configuration (e.g., "summarize" loads
                    "summarize.Cllmfile.yml")
        cllm_path: Optional custom .cllm directory path (from --cllm-path or CLLM_PATH)

    Returns:
        Merged configuration dictionary

    Raises:
        ConfigurationError: If a specified named config doesn't exist or custom path is invalid
    """
    config_files = _find_config_files(config_name, cllm_path)

    if config_name and not config_files:
        # If user explicitly requested a named config but it doesn't exist, error
        if cllm_path:
            raise ConfigurationError(
                f"Configuration '{config_name}' not found in custom path: {cllm_path}\n"
                f"Searched for {config_name}.Cllmfile.yml"
            )
        else:
            raise ConfigurationError(
                f"Configuration '{config_name}' not found. "
                f"Searched for {config_name}.Cllmfile.yml in: "
                f"~/.cllm/, ./.cllm/, ./"
            )

    # Merge configs from lowest to highest precedence
    merged_config: dict[str, Any] = {}
    for config_file in config_files:
        file_config = _load_yaml_file(config_file)
        merged_config.update(file_config)

    return merged_config


def merge_config_with_args(
    config: dict[str, Any], cli_args: dict[str, Any]
) -> dict[str, Any]:
    """Merge configuration file values with CLI arguments.

    CLI arguments take precedence over configuration file values.
    Only non-None CLI arguments override config values.

    Args:
        config: Configuration from file(s)
        cli_args: Arguments from command line

    Returns:
        Merged configuration with CLI args taking precedence
    """
    result = config.copy()

    # CLI args override config values, but only if they're not None
    for key, value in cli_args.items():
        if value is not None:
            result[key] = value

    return result


def get_config_sources(
    config_name: str | None = None, cllm_path: str | None = None
) -> list[str]:
    """Get list of configuration file paths that would be loaded.

    Implements ADR-0016: Configurable .cllm Directory Path

    Useful for --show-config to display where settings came from.

    Args:
        config_name: Optional named configuration
        cllm_path: Optional custom .cllm directory path

    Returns:
        List of configuration file paths as strings
    """
    return [str(path) for path in _find_config_files(config_name, cllm_path)]


def is_remote_schema(path: str) -> bool:
    """Check if path is a remote URL.

    Args:
        path: Path or URL string

    Returns:
        True if path is an HTTP/HTTPS URL
    """
    return path.startswith("https://") or path.startswith("http://")


def get_cache_path(url: str) -> Path:
    """Generate cache file path from URL hash.

    Uses SHA-256 hash of URL to create a unique, filesystem-safe cache filename.

    Args:
        url: Remote schema URL

    Returns:
        Path to cache file
    """
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


def load_remote_schema(url: str) -> dict[str, Any]:
    """Download and cache remote schema with security checks.

    Implements ADR-0006 security measures:
    - HTTPS-only by default (configurable via CLLM_ALLOW_HTTP_SCHEMAS)
    - 1MB size limit
    - 10-second timeout
    - Schema validation before caching
    - TTL-based caching with stale cache fallback

    Args:
        url: HTTPS URL to JSON schema

    Returns:
        Validated JSON schema dictionary

    Raises:
        ConfigurationError: If URL is insecure, download fails, or schema is invalid
    """
    # Security check: HTTPS only by default
    if not url.startswith("https://"):
        allow_http = os.getenv("CLLM_ALLOW_HTTP_SCHEMAS") == "1"
        if not allow_http:
            raise ConfigurationError(
                f"Insecure schema URL (HTTP not allowed): {url}\n"
                f"Suggestion: Use HTTPS URL or set CLLM_ALLOW_HTTP_SCHEMAS=1 to override (not recommended)"
            )

    # Check cache first
    cache_path = get_cache_path(url)
    cache_ttl = int(os.getenv("CLLM_SCHEMA_CACHE_TTL", DEFAULT_CACHE_TTL))

    # Check if we're in offline mode
    offline_mode = os.getenv("CLLM_OFFLINE_MODE") == "1"

    if cache_path.exists():
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age < cache_ttl:
            # Use cached version (within TTL)
            try:
                with open(cache_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                # Cache corrupted, will re-download
                pass

    # If offline mode and no valid cache, error
    if offline_mode:
        if cache_path.exists():
            # Use stale cache in offline mode
            try:
                with open(cache_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        raise ConfigurationError(
            f"Cannot download schema in offline mode: {url}\n"
            f"Cache miss: No cached version available\n"
            f"Suggestion: Disable CLLM_OFFLINE_MODE or use a local schema file"
        )

    # Download schema
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Check size limit
        content_length = len(response.content)
        max_size = int(os.getenv("CLLM_MAX_SCHEMA_SIZE", MAX_SCHEMA_SIZE))
        if content_length > max_size:
            raise ConfigurationError(
                f"Schema too large: {content_length} bytes (max {max_size})\n"
                f"URL: {url}\n"
                f"Suggestion: Use a smaller schema or increase CLLM_MAX_SCHEMA_SIZE"
            )

        # Parse JSON
        schema = response.json()

        # Validate it's a valid JSON Schema
        try:
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as e:
            raise ConfigurationError(
                f"Invalid JSON Schema from {url}\n"
                f"Schema validation error: {e}\n"
                f"Suggestion: Verify URL points to a valid JSON Schema file"
            ) from e

        # Cache the validated schema
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(schema, f)

        return schema

    except requests.Timeout as e:
        # Try stale cache as fallback
        if cache_path.exists():
            try:
                cache_age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
                print(
                    f"Warning: Request timeout, using cached schema from {url} "
                    f"(cached {cache_age_hours:.1f} hours ago)",
                    file=__import__("sys").stderr,
                )
                with open(cache_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        raise ConfigurationError(
            f"Failed to download schema from {url}\n"
            f"Network error: Connection timeout (10s limit)\n"
            f"Cache miss: No cached version available\n"
            f"Suggestion: Check network connection or use a local schema file"
        ) from e

    except requests.RequestException as e:
        # Try stale cache as fallback
        if cache_path.exists():
            try:
                cache_age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
                print(
                    f"Warning: Network error, using cached schema from {url} "
                    f"(cached {cache_age_hours:.1f} hours ago)",
                    file=__import__("sys").stderr,
                )
                with open(cache_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        raise ConfigurationError(
            f"Failed to download schema from {url}\n"
            f"Network error: {e}\n"
            f"Cache miss: No cached version available\n"
            f"Suggestion: Check network connection or use a local schema file"
        ) from e

    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Invalid JSON from {url}\n"
            f"Parse error: {e}\n"
            f"Suggestion: Verify URL returns valid JSON content"
        ) from e


def clear_schema_cache() -> int:
    """Clear all cached schemas.

    Returns:
        Number of cached schemas cleared
    """
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            cache_file.unlink()
            count += 1
        except OSError:
            pass

    return count


def resolve_schema_file_path(schema_file: str) -> Path:
    """Resolve schema file path with fallback lookup logic.

    For relative paths, checks:
    1. Current working directory (where cllm is executed)
    2. .cllm folder root

    Absolute paths are used as-is.

    Args:
        schema_file: Path to schema file (relative or absolute)

    Returns:
        Resolved Path object

    Raises:
        ConfigurationError: If schema file cannot be found
    """
    schema_path = Path(schema_file)

    # If absolute path, use as-is
    if schema_path.is_absolute():
        if not schema_path.exists():
            raise ConfigurationError(f"Schema file not found: {schema_file}")
        return schema_path

    # For relative paths, check CWD first, then .cllm folder
    search_paths = [
        Path.cwd() / schema_file,
        Path.cwd() / ".cllm" / schema_file,
    ]

    for path in search_paths:
        if path.exists() and path.is_file():
            return path

    # If not found, raise error with helpful message
    raise ConfigurationError(
        f"Schema file not found: {schema_file}\n"
        f"Searched in:\n"
        f"  - {search_paths[0]}\n"
        f"  - {search_paths[1]}"
    )


def load_json_schema(schema_source: Any) -> dict[str, Any]:
    """Load and validate a JSON schema from various sources.

    Supports local files and remote URLs (ADR-0006).

    Args:
        schema_source: Can be:
            - dict: Already parsed schema (from YAML config)
            - str: Path to JSON schema file OR HTTPS URL
            - Path: Path object to JSON schema file

    Returns:
        Validated JSON schema as dictionary

    Raises:
        ConfigurationError: If schema is invalid or cannot be loaded
    """
    # If already a dict, validate and return
    if isinstance(schema_source, dict):
        try:
            # Validate that it's a valid JSON Schema
            jsonschema.Draft7Validator.check_schema(schema_source)
            return schema_source
        except jsonschema.exceptions.SchemaError as e:
            raise ConfigurationError(f"Invalid JSON schema: {e}") from e

    # If string or Path, check if it's a URL or local file
    if isinstance(schema_source, (str, Path)):
        schema_str = str(schema_source)

        # Check if it's a remote URL (ADR-0006)
        if is_remote_schema(schema_str):
            return load_remote_schema(schema_str)

        # Otherwise, load from local file
        schema_path = resolve_schema_file_path(schema_str)
        try:
            with open(schema_path) as f:
                schema = json.load(f)
            # Validate the loaded schema
            jsonschema.Draft7Validator.check_schema(schema)
            return schema
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in schema file {schema_path}: {e}"
            ) from e
        except jsonschema.exceptions.SchemaError as e:
            raise ConfigurationError(
                f"Invalid JSON schema in {schema_path}: {e}"
            ) from e
        except OSError as e:
            raise ConfigurationError(
                f"Error reading schema file {schema_path}: {e}"
            ) from e

    raise ConfigurationError(
        f"Invalid schema source type: {type(schema_source)}. "
        f"Expected dict, str, or Path."
    )


def validate_against_schema(data: Any, schema: dict[str, Any]) -> None:
    """Validate data against a JSON schema.

    Args:
        data: Data to validate (typically parsed JSON from LLM response)
        schema: JSON schema to validate against

    Raises:
        ConfigurationError: If validation fails
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ConfigurationError(f"Schema validation failed: {e.message}") from e
