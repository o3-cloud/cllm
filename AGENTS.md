# Repository Guidelines

## Project Structure & Module Organization

CLLM follows a src-layout. CLI entrypoints and provider integrations live under `src/cllm/`; start in `cli.py` and the provider subpackages when adding commands or chaining logic. Tests for each module belong in `tests/`, mirroring package paths (`tests/test_cli.py`, `tests/conversation/test_store.py`). Reference material and longer-form guides sit in `docs/`, while `examples/` contains runnable shell pipelines. Built wheels and other artifacts land in `dist/`; avoid editing generated files directly.

## Build, Test, and Development Commands

Use uv for environment management. `uv sync` resolves dependencies declared in `pyproject.toml`. Run the CLI locally with `uv run cllm --help` to confirm argument wiring. Execute the default test suite with `uv run pytest`; add `-k name` when narrowing focus. Build distributable artifacts via `uv build`, which uses Hatchling under the hood. If you change console entrypoints, run `uv run python -m cllm.cli "What is new?"` to validate packaging metadata.

## Coding Style & Naming Conventions

Write Python with PEP 8 defaults: four-space indentation, `lower_snake_case` for functions and modules, and `CapWords` for classes. Shared helpers belong under `src/cllm/utils/` to keep the CLI surface small. Prefer explicit type hints on public functions; they improve generated help output and downstream tooling. Keep YAML and JSON samples under `examples/` named `*-sample.{yml,json}` for quick discovery.

## Testing Guidelines

Tests rely on `pytest` with `pytest-asyncio` where async clients are involved. Name files `test_*.py`, functions `test_*`, and co-locate fixtures in `tests/conftest.py`. Cover new providers or CLI flags with at least one integration-style test that exercises `uv run cllm` through `CliRunner` or subprocess shims. When touching ADR-backed features, add assertions around persisted state under `.cllm/` paths.

## Commit & Pull Request Guidelines

Follow the conventional-commit pattern visible in history (`feat(conversation): ...`, `docs(adr): ...`). Reference relevant ADR numbers or issue IDs in the message body when applicable. PRs should include: a succinct summary, test evidence (command snippets), and screenshots or sample transcripts for CLI UX changes. Request review from maintainers of affected modules and link to any provider-specific configuration docs.

## Architecture Decisions

Architecture Decision Records live in `docs/decisions/`; filenames follow `000N-title.md` and double as identifiers. Before altering cross-cutting behavior (config precedence, provider abstractions, conversation storage), read the relevant ADR to understand rationale and guardrails. Substantial design shifts should include a new sequential ADR draft plus a `docs(adr):` commit, then be linked in the pull request alongside the implementation.
