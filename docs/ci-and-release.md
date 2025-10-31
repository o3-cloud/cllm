# CI and Release Guide

This document describes how the GitHub Actions workflows introduced with ADR-0019 operate and how to use them day-to-day.

## Continuous Integration (`ci.yml`)

- **Triggers**: Pull requests targeting `main` and direct pushes to `main`.
- **Jobs**:
  - `Ruff Lint` runs `uv run --dev ruff check .` on Python 3.12.
  - `Mypy Type Check` enforces the strict mypy configuration maintained in `pyproject.toml`.
  - `Pytest` executes the full suite on Python 3.8–3.12 with coverage (`coverage.xml` is uploaded per interpreter).
- **Tooling**: Each job installs dependencies with `uv sync --dev --frozen`, leveraging the checked-in `uv.lock` for reproducible environments.
- **Expected duration**: Under 5 minutes in aggregate for PR validation (matrix jobs run in parallel).

## Release Automation (`release.yml`)

- **Trigger**: Pushing a tag that matches `v*` (for example `v0.1.7`).
- **Permissions**: Uses GitHub’s trusted publisher flow (`id-token: write`) via `pypa/gh-action-pypi-publish`.
- **Steps**:
  1. Install dependencies with `uv sync --frozen --dev`.
  2. Build wheel and sdist via `uv build`.
  3. Upload the `dist/` contents as a workflow artifact.
  4. Publish the build to PyPI.

### Cutting a Release

1. Update the project version (e.g., `pyproject.toml`) and changelog as needed.
2. Commit the changes and create an annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
3. Push the branch and tag: `git push origin <branch> && git push origin vX.Y.Z`.
4. Monitor the **Release** workflow in GitHub Actions; it should complete without manual intervention.

> **Prerequisite:** Configure PyPI trusted publishing for this repository so the workflow’s OIDC token is authorized to upload the package. No API tokens are stored in secrets.

### Dry Runs

For confidence before tagging:

- `uv build` locally ensures wheels build successfully.
- `uv run --dev pytest` and `uv run --dev ruff check .` mirror the CI checks.
- `uv run --dev mypy` exercises the strict type-checking configuration.
