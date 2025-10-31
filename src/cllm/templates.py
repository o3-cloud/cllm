"""Jinja2 template rendering for variable expansion in commands.

Implements ADR-0012: Variable Expansion in Context Commands with Jinja2 Templates
"""

import shlex
from typing import Any, Dict

from jinja2 import StrictUndefined, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment


class TemplateError(Exception):
    """Raised when there's an error rendering a template."""

    pass


def create_jinja_env() -> SandboxedEnvironment:
    """Create a sandboxed Jinja2 environment for secure template rendering.

    - SandboxedEnvironment prevents dangerous operations (file access, code execution)
    - StrictUndefined raises errors for undefined variables (fail fast)
    - Custom filters for shell operations

    Returns:
        Configured SandboxedEnvironment instance
    """
    env = SandboxedEnvironment(
        undefined=StrictUndefined,
        autoescape=False,  # We're generating shell commands, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filter for shell escaping
    env.filters["shellquote"] = shlex.quote

    return env


# Lazily re-use a sandboxed environment for rendering commands
_SANDBOX_ENV: SandboxedEnvironment = create_jinja_env()


def _coerce_scalar(value: str) -> Any:
    """Best-effort conversion of string values to booleans or numbers."""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    if value.isdigit():
        try:
            return int(value)
        except ValueError:
            pass

    numeric_candidate = value.replace(".", "", 1).replace("-", "", 1)
    if numeric_candidate.isdigit() and value.count(".") <= 1:
        try:
            return float(value)
        except ValueError:
            pass

    return value


def build_template_context(
    cli_vars: Dict[str, Any],
    config_vars: Dict[str, Any],
    env_vars: Dict[str, str],
) -> Dict[str, Any]:
    """Build Jinja2 context dict with precedence: CLI > Config > Environment.

    Args:
        cli_vars: Variables from --var CLI flags
        config_vars: Variables from Cllmfile.yml (may contain None for required vars)
        env_vars: Environment variables

    Returns:
        Dict[str, Any]: Resolved variable context for rendering templates

    Raises:
        TemplateError: If required variable (config value is None) is not provided
    """
    context = {}

    # Start with config defaults
    for var_name, config_value in config_vars.items():
        # Required variable (None) - must come from CLI or env
        if config_value is None:
            if var_name in cli_vars:
                context[var_name] = cli_vars[var_name]
            elif var_name in env_vars:
                context[var_name] = _coerce_scalar(env_vars[var_name])
            else:
                raise TemplateError(
                    f"Required variable '{var_name}' not provided via --var flag or environment\n\n"
                    f"  Declare it in your command:\n"
                    f"    cllm ... --var {var_name}=value\n\n"
                    f"  Or set it as environment variable:\n"
                    f"    export {var_name}=value"
                )
        else:
            context[var_name] = config_value

    # Override with environment variables
    for var_name in config_vars.keys():
        if var_name in env_vars:
            context[var_name] = _coerce_scalar(env_vars[var_name])

    # Override with CLI variables (highest precedence)
    context.update(cli_vars)

    return context


def render_command_template(command_template: str, context: Dict[str, Any]) -> str:
    """Render a Jinja2 template with variable context.

    Args:
        command_template: Jinja2 template string (e.g., "cat {{ FILE }} | head")
        context: Dict of variables (e.g., {"FILE": "test.py"})

    Returns:
        Rendered command string with variables expanded

    Raises:
        TemplateError: If template has syntax errors or undefined variables
    """
    try:
        template = _SANDBOX_ENV.from_string(command_template)
        rendered = template.render(context)
        return rendered.strip()
    except TemplateSyntaxError as e:
        raise TemplateError(
            f"Template syntax error in command: {e.message} (line {e.lineno})\n\n"
            f"  Check your template syntax:\n"
            f"    - Variables: {{{{ VAR_NAME }}}}\n"
            f"    - Conditionals: {{% if CONDITION %}}...{{% endif %}}\n"
            f"    - Filters: {{{{ VAR | filter }}}}\n\n"
            f"  See Jinja2 docs: https://jinja.palletsprojects.com/"
        ) from e
    except UndefinedError as e:
        # Extract variable name from error message if possible
        error_msg = str(e)
        raise TemplateError(
            f"Undefined variable in command template: {error_msg}\n\n"
            f"  Add missing variable:\n"
            f"    cllm ... --var VARIABLE_NAME=value\n\n"
            f"  Or declare it in Cllmfile.yml:\n"
            f"    variables:\n"
            f"      VARIABLE_NAME: default_value"
        ) from e
    except Exception as e:
        # Catch any other Jinja2 errors
        raise TemplateError(f"Error rendering template: {e}") from e


def get_available_variables_description(context: Dict[str, Any]) -> str:
    """Generate a formatted description of available variables for error messages.

    Args:
        context: Current template context

    Returns:
        Formatted string describing available variables
    """
    if not context:
        return "  No variables defined"

    lines = ["  Available variables:"]
    for var_name, var_value in sorted(context.items()):
        # Truncate long values for display
        value_str = str(var_value)
        if len(value_str) > 50:
            value_str = value_str[:47] + "..."
        lines.append(f"    - {var_name}: {value_str}")

    return "\n".join(lines)
