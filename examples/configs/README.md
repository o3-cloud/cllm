# CLLM Configuration Examples

This directory contains example `Cllmfile.yml` configuration files demonstrating various use cases for CLLM.

## Quick Start

### Using Named Configurations

Copy any of these files to your project directory and use them with the `--config` flag:

```bash
# Summarize a document
cat document.txt | cllm --config summarize

# Generate creative writing
echo "Write a story about a robot" | cllm --config creative

# Review code changes
git diff | cllm --config code-review
```

### Using Default Configuration

Copy `Cllmfile.yml` to one of these locations:

1. `./Cllmfile.yml` - Project-specific config (highest precedence)
2. `./.cllm/Cllmfile.yml` - Project .cllm folder
3. `~/.cllm/Cllmfile.yml` - User-wide config (lowest precedence)

Then simply run:

```bash
echo "Your prompt" | cllm
```

## Configuration Files

### `Cllmfile.yml` - Default Configuration

General-purpose configuration with common settings commented out. Good starting point for customization.

**Key features:**

- GPT-3.5-turbo with balanced parameters
- Retry logic for reliability
- Extensive commented examples

### `summarize.Cllmfile.yml` - Text Summarization

Optimized for concise, accurate summarization of documents and articles.

**Key features:**

- Claude Sonnet for quality
- Low temperature (0.3) for factual accuracy
- Limited max tokens (500) for brevity
- System message guiding summarization style

**Usage:**

```bash
cat article.md | cllm --config summarize
cllm --config summarize < research-paper.txt
```

### `creative.Cllmfile.yml` - Creative Writing

Tuned for imaginative, engaging storytelling and creative content.

**Key features:**

- GPT-4 for creative capability
- High temperature (1.2) for variety
- Nucleus sampling (top_p: 0.95)
- Extended max tokens (2000) for long-form content
- System message encouraging creativity

**Usage:**

```bash
echo "Write a sci-fi story about time travel" | cllm --config creative
cllm --config creative "Generate 5 creative business names for a bakery"
```

### `code-review.Cllmfile.yml` - Code Review

Configured for thorough code analysis and constructive feedback.

**Key features:**

- GPT-4 for code understanding
- Moderate temperature (0.5) for balanced analysis
- System message with structured review framework
- Covers bugs, best practices, performance, security

**Usage:**

```bash
git diff | cllm --config code-review
cat src/myfile.py | cllm --config code-review
cllm --config code-review < pull-request.diff
```

## Configuration Precedence

Settings are loaded and merged in this order (later sources override earlier ones):

1. `~/.cllm/Cllmfile.yml` (user-wide defaults)
2. `./.cllm/Cllmfile.yml` (project defaults)
3. `./Cllmfile.yml` (project root)
4. Named configs via `--config <name>`
5. CLI flags (highest priority)

**Example:**

```bash
# Config says temperature: 0.3, CLI overrides to 0.9
cllm --config summarize --temperature 0.9 < document.txt
```

## Environment Variables

Configurations support environment variable interpolation using `${VAR_NAME}` syntax:

```yaml
api_key: "${OPENAI_API_KEY}"
api_base: "${CUSTOM_API_BASE}"

extra_headers:
  Authorization: "Bearer ${CUSTOM_TOKEN}"
```

## Viewing Effective Configuration

Use `--show-config` to see the merged configuration and source files:

```bash
cllm --config summarize --show-config

# Output:
# Configuration sources (in order of precedence):
#   - /Users/you/project/summarize.Cllmfile.yml
#
# Effective configuration:
# {
#   "model": "claude-3-sonnet-20240229",
#   "temperature": 0.3,
#   "max_tokens": 500,
#   ...
# }
```

## Creating Custom Configurations

1. Copy an existing example as a template
2. Modify parameters for your use case
3. Save as `<name>.Cllmfile.yml`
4. Use with `cllm --config <name>`

**Example custom config for technical documentation:**

```yaml
# docs.Cllmfile.yml
model: "gpt-4"
temperature: 0.4
max_tokens: 1200

default_system_message: |
  You are a technical documentation writer. Write clear,
  concise documentation with:
  - Step-by-step instructions
  - Code examples
  - Expected outputs
  - Common pitfalls

timeout: 90
num_retries: 2
fallbacks:
  - "claude-3-sonnet-20240229"
```

Usage:

```bash
echo "Document the user authentication API" | cllm --config docs
```

## Available Configuration Options

See the [ADR-0003 specification](../../docs/decisions/0003-cllmfile-configuration-system.md) for the complete list of supported options including:

- Model selection and fallbacks
- Sampling parameters (temperature, top_p, seed)
- Output control (max_tokens, stop sequences)
- Response penalties (frequency_penalty, presence_penalty)
- Streaming configuration
- Authentication and API endpoints
- Retry and timeout settings
- Metadata and logging
- Custom HTTP headers

## Tips

1. **Start simple**: Begin with basic settings (model, temperature, max_tokens)
2. **Use comments**: Document why you chose specific values
3. **Version control**: Commit project configs to share with your team
4. **Test fallbacks**: Ensure backup models work for your use case
5. **Environment-specific**: Use different configs for dev/staging/prod

## Further Reading

- [ADR-0003: Cllmfile Configuration System](../../docs/decisions/0003-cllmfile-configuration-system.md)
- [LiteLLM Provider Documentation](https://docs.litellm.ai/docs/providers)
- [LiteLLM Completion Parameters](https://docs.litellm.ai/docs/completion/input)
