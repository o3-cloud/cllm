# Add Bash Script Examples for CLLM CLI Workflows

## Context and Problem Statement

Teams adopting CLLM often integrate the CLI into shell pipelines, CI jobs, and local automation scripts. Today we document patterns in prose, but we do not ship opinionated, runnable bash examples. Without concrete scripts, contributors duplicate work, invent inconsistent conventions, and struggle to discover best practices for error handling, environment configuration, and piping data into `cllm`.

## Decision Drivers

- **CLI-first onboarding**: New users should be able to copy, run, and adapt working scripts within minutes.
- **Repeatable automation**: Provide patterns for CI/CD and local automation that survive shell quirks.
- **Documentation completeness**: Examples should live next to the code so they evolve with the implementation.
- **Cross-platform shell support**: Prefer POSIX-compatible bash that works on macOS and common Linux distros.
- **Testability**: Examples need lightweight validation so they do not rot.

## Considered Options

1. Continue relying on narrative documentation and ad-hoc snippets embedded in READMEs.
2. Publish examples as external gists referenced from the docs.
3. Ship curated bash scripts inside the repository under `examples/`.

## Decision Outcome

Chosen option: **Ship curated bash scripts inside the repository (`examples/`)**.

### Consequences

- Good: Examples live under version control, making updates reviewable and synchronized with feature changes.
- Good: Scripts demonstrate recommended flags (`cllm`, `--conversation`, `--output`) with robust defaults (`set -euo pipefail`).
- Good: CI can execute smoke tests to ensure scripts keep working as the CLI evolves.
- Good: Documentation can deep-link to specific scripts, improving discoverability.
- Bad: We must maintain portability; bash constructs that rely on GNU extensions need guards or fallbacks.
- Bad: Scripts require ongoing ownership to keep instructions current with provider configuration changes.

## Implementation Details

- Create a dedicated `examples/bash/` directory for shell workflows. Each script includes:
  - Shebang `#!/usr/bin/env bash`.
  - `set -euo pipefail` and minimal inline comments explaining inputs/outputs.
  - Usage documentation in the header block and references to relevant ADRs/config files.
- Provide at least three starter scenarios:
  1. **`examples/bash/prompt-loop.sh`** – interactive loop that appends prompts to a conversation ID.
  2. **`examples/bash/git-diff-review.sh`** – pipes `git diff` into `cllm` for review suggestions.
  3. **`examples/bash/cron-digest.sh`** – schedules a daily status summary using environment variables for provider selection.
- Add a README section that links to the scripts and explains how to run them with plain `bash` (assuming the `cllm` entrypoint is installed and on `PATH`).
- Introduce a low-cost smoke test (pytest or shell) that runs each script in dry-run mode using the mock provider to assure compatibility.
- Encourage contributors to append new examples by following the same structure and adding brief tests.

## Status

Accepted.

## Consequences for Future Work

- When adding new CLI flags or providers, update relevant scripts and their smoke tests.
- Consider expanding coverage to zsh and fish once bash examples stabilize.
- If scripts grow complex, promote reusable helpers into `src/cllm/utils/` and import them via `uv run python -m`.
