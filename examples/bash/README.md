# Bash Workflows

Curated shell scripts that showcase common CLLM CLI integrations. Each script uses the installed `cllm` entrypoint and is safe to run from macOS or most Linux distributions. All scripts accept the `CLLM_EXAMPLE_DRY_RUN=1` environment variable to skip live API calls and print the command that would have been executed—handy for CI smoke tests.

> **Prerequisite:** Activate the virtual environment where `cllm` is installed so the command is available on `PATH`.

## Scripts

### prompt-loop.sh

Interactive REPL that keeps history under a conversation ID.

```bash
CLLM_MODEL=claude-3-sonnet-20240229 bash examples/bash/prompt-loop.sh notebook
```

Type `:quit` or `:exit` to leave the session. Extra flags (schema enforcement, temperature, etc.) can be passed via `CLLM_EXTRA_FLAGS="--temperature 0.4"`.

### git-diff-review.sh

Pairs with `git diff` to request review feedback.

```bash
bash examples/bash/git-diff-review.sh --cached
```

Customise the instructions with `CLLM_REVIEW_PROMPT`, switch models via `CLLM_MODEL`, or persist context using `CLLM_REVIEW_CONVERSATION`.

### cron-digest.sh

Summarises daily activity pulled from a shell command—perfect for cron jobs.

```bash
CLLM_DIGEST_SOURCE_CMD='gh pr list --state merged --json title --limit 10 | jq -r ".[] | \"- \" + .title"' \
  bash examples/bash/cron-digest.sh ~/Reports/daily.md
```

Use `--dry-run` or set `CLLM_EXAMPLE_DRY_RUN=1` to preview the prompt without making a request.

### templated-context.sh

Demonstrates ADR-0012 by rendering Jinja2 templates inside context commands. Variables are provided via `--var` flags, letting you reuse the same workflow for different files or branches.

```bash
CLLM_EXAMPLE_DRY_RUN=1 bash examples/bash/templated-context.sh src/cllm/cli.py --branch main --verbose
```

The script expands commands like `git diff {{ BRANCH }}..HEAD -- {{ FILE_PATH }}` and `cat {{ FILE_PATH }}` with optional line numbers, showcasing filters (`| shellquote`) and conditionals (`{% if VERBOSE %}`).

## Smoke testing

Run lightweight checks without hitting the API:

```bash
CLLM_EXAMPLE_DRY_RUN=1 bash examples/bash/git-diff-review.sh main..HEAD
CLLM_EXAMPLE_DRY_RUN=1 bash examples/bash/cron-digest.sh --dry-run
printf 'hello\n:quit\n' | CLLM_EXAMPLE_DRY_RUN=1 bash examples/bash/prompt-loop.sh demo
```

These commands are also exercised via `pytest` to ensure scripts remain runnable as the CLI evolves.
