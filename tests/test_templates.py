"""
Tests for the templating utilities (ADR-0012).
"""

import pytest

from cllm.templates import (
    TemplateError,
    build_template_context,
    get_available_variables_description,
    render_command_template,
)


class TestBuildTemplateContext:
    """Unit tests for building the template context."""

    def test_precedence_cli_over_env_and_config(self):
        """CLI variables should override environment and config defaults."""
        cli_vars = {"BRANCH": "feature/login", "EXTRA": 42}
        config_vars = {
            "FILE_PATH": "README.md",
            "BRANCH": "main",
            "REQUIRED": None,
            "MAX_LINES": 10,
        }
        env_vars = {"BRANCH": "bugfix", "REQUIRED": "abc123", "MAX_LINES": "25"}

        context = build_template_context(cli_vars, config_vars, env_vars)

        assert context["FILE_PATH"] == "README.md"
        assert context["BRANCH"] == "feature/login"  # CLI overrides env/config
        assert context["REQUIRED"] == "abc123"  # Required filled from env
        assert context["MAX_LINES"] == 25  # Env value coerced to int
        assert context["EXTRA"] == 42  # CLI variable not declared in config preserved

    def test_missing_required_variable_raises(self):
        """Required variables without CLI/env values should raise TemplateError."""
        cli_vars = {}
        config_vars = {"REQUIRED": None}
        env_vars = {}

        with pytest.raises(TemplateError, match="Required variable 'REQUIRED'"):
            build_template_context(cli_vars, config_vars, env_vars)


class TestRenderCommandTemplate:
    """Unit tests for template rendering."""

    def test_basic_rendering_with_filters(self):
        """Render template with shellquote filter and conditionals."""
        context = {"FILE_PATH": "docs/adr 0012.md", "VERBOSE": False}

        rendered = render_command_template(
            "cat {{ FILE_PATH | shellquote }} {% if VERBOSE %}-n{% endif %}",
            context,
        )

        assert rendered == "cat 'docs/adr 0012.md'"

    def test_missing_variable_raises_template_error(self):
        """Undefined variables should raise TemplateError with helpful message."""
        context = {}

        with pytest.raises(TemplateError, match="Undefined variable"):
            render_command_template("cat {{ MISSING_VAR }}", context)


class TestAvailableVariablesDescription:
    """Unit tests for helper that formats available variables."""

    def test_description_with_values(self):
        """Ensure description enumerates context variables."""
        description = get_available_variables_description(
            {"FILE": "README.md", "MAX": 10}
        )

        assert "Available variables" in description
        assert "- FILE: README.md" in description
        assert "- MAX: 10" in description

    def test_description_when_empty(self):
        """Empty context should return friendly message."""
        description = get_available_variables_description({})

        assert description.strip() == "No variables defined"
