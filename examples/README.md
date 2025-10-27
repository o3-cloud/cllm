# CLLM Examples

This directory showcases ways to use CLLM from both the CLI and Python. Pick the path that suits your workflow, copy the snippets, and adapt.

## Prerequisites

1. Install CLLM into your local environment:

   ```bash
   uv pip install -e .
   ```

2. Export the provider API keys you plan to use:

   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GOOGLE_API_KEY="your-google-key"
   # ... other providers as needed
   ```

3. Confirm the CLI entrypoint is wired up:

   ```bash
   uv run cllm --help
   ```

## Quick CLI recipes

All commands run from the project root. Prefix with `uv run` when you need the managed environment.

- Issue a quick completion with the default model:

  ```bash
  cllm "List three fun bash prompts for agents."
  ```

- Switch providers by passing `--model`:

  ```bash
  cllm "Compare Claude and Gemini release dates." --model claude-3-sonnet-20240229
  ```

- Stream the response for long-form answers:

  ```bash
  echo "Explain how LiteLLM normalizes provider APIs." | cllm --stream --model gpt-4
  ```

- Validate a JSON schema provided in `examples/schemas`:

  ```bash
  cllm --validate-schema --json-schema-file examples/schemas/entity-extraction.json
  ```

- Enforce structured output with a schema:

  ```bash
  cllm \
    "Extract people and companies mentioned in the text." \
    --json-schema-file examples/schemas/entity-extraction.json \
    --model gpt-4
  ```

- Use a named configuration from `examples/configs` (run inside that directory so discovery finds the file):

  ```bash
  (cd examples/configs && cllm --config summarize "Summarize the latest ADR in three bullets.")
  ```

- Work with saved conversations:

  ```bash
  cllm "Draft a release note outline." --conversation launch-notes
  cllm --show-conversation launch-notes
  cllm --list-conversations
  ```

## Bash workflows

Reusable shell automations live in `examples/bash/`. Each script uses the installed `cllm` command and supports dry-run mode via `CLLM_EXAMPLE_DRY_RUN=1` for CI safety.

- `prompt-loop.sh` – interactive REPL that stores prompts under a conversation ID
- `git-diff-review.sh` – pipes `git diff` output to `cllm` for actionable review notes
- `cron-digest.sh` – compiles daily summaries from any shell command, suitable for cron

See `examples/bash/README.md` for usage, environment knobs, and smoke-test invocations.

## Programmatic samples

Python scripts remain available when you need to embed CLLM inside larger workflows:

- `examples/basic_usage.py` – synchronous completions, streaming, temperature control
- `examples/async_usage.py` – concurrent provider queries with `asyncio`
- `examples/provider_comparison.py` – side-by-side provider responses
- `examples/structured_output_usage.py` – schema-enforced completions

Run the scripts with:

```bash
uv run python examples/basic_usage.py
```

## Key concepts

- LiteLLM model names are provider-specific (see https://docs.litellm.ai/docs/providers).
- All examples rely on the shared `LLMClient` abstraction (ADR-0002).
- Errors for providers without configured keys are expected and surfaced clearly.

## Ideas for future examples

- End-to-end shell pipeline that feeds `git diff` into `cllm --config code-review`.
- Demonstration of inline `--json-schema` strings for lightweight extraction.
- Conversation handoff example that exports a transcript for follow-up prompts.
- CI-focused smoke test showing how to fail builds when schema validation fails.
