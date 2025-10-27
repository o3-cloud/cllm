"""Configuration file loading and merging for CLLM.

Implements ADR-0003: Cllmfile Configuration System
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigurationError(Exception):
    """Raised when there's an error loading or parsing configuration files."""

    pass


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

        def replacer(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replacer, value)
    elif isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    else:
        return value


def _load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML configuration file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary of configuration values

    Raises:
        ConfigurationError: If file cannot be read or parsed
    """
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
            if config is None:
                return {}
            if not isinstance(config, dict):
                raise ConfigurationError(
                    f"Configuration file {file_path} must contain a YAML dictionary"
                )
            return _interpolate_env_vars(config)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Error parsing YAML file {file_path}: {e}")
    except OSError as e:
        raise ConfigurationError(f"Error reading file {file_path}: {e}")


def _find_config_files(config_name: Optional[str] = None) -> list[Path]:
    """Find all applicable configuration files in order of precedence.

    Search order (lowest to highest precedence):
    1. ~/.cllm/Cllmfile.yml (or ~/.cllm/<name>.Cllmfile.yml)
    2. ./.cllm/Cllmfile.yml (or ./.cllm/<name>.Cllmfile.yml)
    3. ./Cllmfile.yml (or ./<name>.Cllmfile.yml)

    Args:
        config_name: Optional named configuration (e.g., "summarize")

    Returns:
        List of existing config file paths, in order from lowest to highest precedence
    """
    if config_name:
        filename = f"{config_name}.Cllmfile.yml"
    else:
        filename = "Cllmfile.yml"

    search_paths = [
        Path.home() / ".cllm" / filename,  # User home
        Path.cwd() / ".cllm" / filename,  # Project .cllm folder
        Path.cwd() / filename,  # Current directory
    ]

    # Return only files that exist, in order
    return [path for path in search_paths if path.exists() and path.is_file()]


def load_config(config_name: Optional[str] = None) -> Dict[str, Any]:
    """Load and merge configuration files.

    Configurations are loaded from multiple locations and merged with later
    files taking precedence. CLI arguments should override these values.

    Args:
        config_name: Optional named configuration (e.g., "summarize" loads
                    "summarize.Cllmfile.yml")

    Returns:
        Merged configuration dictionary

    Raises:
        ConfigurationError: If a specified named config doesn't exist
    """
    config_files = _find_config_files(config_name)

    if config_name and not config_files:
        # If user explicitly requested a named config but it doesn't exist, error
        raise ConfigurationError(
            f"Configuration '{config_name}' not found. "
            f"Searched for {config_name}.Cllmfile.yml in: "
            f"~/.cllm/, ./.cllm/, ./"
        )

    # Merge configs from lowest to highest precedence
    merged_config: Dict[str, Any] = {}
    for config_file in config_files:
        file_config = _load_yaml_file(config_file)
        merged_config.update(file_config)

    return merged_config


def merge_config_with_args(
    config: Dict[str, Any], cli_args: Dict[str, Any]
) -> Dict[str, Any]:
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


def get_config_sources(config_name: Optional[str] = None) -> list[str]:
    """Get list of configuration file paths that would be loaded.

    Useful for --show-config to display where settings came from.

    Args:
        config_name: Optional named configuration

    Returns:
        List of configuration file paths as strings
    """
    return [str(path) for path in _find_config_files(config_name)]
