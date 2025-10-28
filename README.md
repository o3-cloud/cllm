# CLLM - Command Line LLM Interface

A bash-centric command-line interface for interacting with large language models across 100+ providers. Chain LLM calls using familiar bash piping and scripting techniques.

## Overview

CLLM bridges the gap between ChatGPT GUIs and complex automation by providing transparency and bash integration for AI workflows. It's designed for developers who want programmatic control over LLM interactions without leaving their terminal - whether for quick one-liners, sophisticated pipelines, or CI/CD integration.

## Table of Contents

- [Features](#features)
- [Key Concepts](#key-concepts)
- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Basic Usage](#basic-usage)
  - [Conversation Threading](#conversation-threading)
  - [Debugging & Troubleshooting](#debugging--troubleshooting)
  - [Python API](#python-api)
- [Advanced Usage](#advanced-usage)
  - [LLM Chaining](#llm-chaining-with-bash-pipes)
  - [Bash Script Examples](#bash-script-examples)
  - [Structured Output](#structured-output-with-json-schema)
  - [Configuration Files](#configuration-files-cllmfileyml)
- [CLI Reference](#cli-reference)
- [Providers & Models](#providers--models)
- [Development](#development)
- [Architecture Decision Records](#architecture-decision-records)

## Features

- **🚀 Simple CLI Interface**: Generate text from prompts with straightforward commands
- **🔗 LLM Chaining**: Chain multiple LLM calls using bash pipes and scripts
- **📋 Structured Output**: Get guaranteed JSON output conforming to JSON Schema specifications
- **💬 Conversation Threading**: Multi-turn conversations with automatic context management
- **⚡ Real-time Streaming**: Stream responses as they're generated for long-form content
- **🔍 Debugging & Logging**: Built-in debug mode with structured JSON logging
- **🏢 Multi-Provider Support** (100+ providers via LiteLLM):
  - OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo, GPT-4o)
  - Anthropic (Claude 3 Haiku, Sonnet, Opus, 3.5 Sonnet)
  - Google (Gemini Pro, 1.5 Pro, 1.5 Flash)
  - Groq (Mixtral, Llama 3)
  - AWS Bedrock
  - Azure OpenAI
  - Local Ollama models
  - And 90+ more providers
- **⚙️ Flexible Configuration**: Shareable Cllmfile.yml configs with environment variable interpolation
- **📜 Bash Scripts Library**: Curated examples for common workflows (git-diff review, prompt loops, etc.)
- **🔧 Developer-Friendly**: Modern Python packaging with `uv`, comprehensive test suite

## Key Concepts

### Provider Abstraction (ADR-0002)

CLLM uses [LiteLLM](https://github.com/BerriAI/litellm) to provide a unified interface across 100+ LLM providers. This means:

- **Same code works everywhere**: Switch from OpenAI to Claude by just changing the model name
- **No provider-specific SDKs**: One interface, one API, all providers
- **Automatic format translation**: All responses follow a consistent format

```bash
# Same command, different providers
cllm --model gpt-4 "Hello"                          # OpenAI
cllm --model claude-3-5-sonnet-20240620 "Hello"    # Anthropic
cllm --model gemini-pro "Hello"                     # Google
cllm --model groq/llama-3.1-70b-versatile "Hello"  # Groq
```

### Bash-First Design

CLLM is optimized for command-line and scripting workflows:

- **Stdin/stdout piping**: `cat file.txt | cllm "Summarize" > summary.txt`
- **Exit codes**: Proper error codes for scripts and CI/CD
- **No GUI required**: All features accessible via CLI flags
- **Composable**: Chain multiple LLM calls using Unix pipes

### Configuration Precedence

Settings are merged from multiple sources (lowest to highest priority):

1. `~/.cllm/Cllmfile.yml` (global defaults)
2. `./.cllm/Cllmfile.yml` (project-specific)
3. `./Cllmfile.yml` (current directory)
4. Environment variables (`CLLM_*`)
5. CLI arguments (always win)

This allows you to set global defaults, override per-project, and customize per-command.

## Requirements

- Python 3.8 or higher
- API keys for your chosen LLM provider(s)
- `uv` (recommended for development - [installation](https://github.com/astral-sh/uv#installation))

## Installation

### Via pip (when published)

```bash
pip install cllm
```

### From source (current method)

```bash
git clone https://github.com/o3-cloud/cllm.git
cd cllm
uv sync

# Run locally
uv run cllm "Hello world"

# Or install globally
uv pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Simple prompt (uses gpt-3.5-turbo by default)
cllm "What is the capital of France?"

# Discover available models
cllm --list-models
cllm --list-models | grep gpt-4  # Filter to specific models

# Use a specific model
cllm --model gpt-4 "Explain quantum computing"

# Use a different provider (same interface!)
cllm --model claude-3-5-sonnet-20240620 "Write a haiku"
cllm --model gemini-pro "Tell me a joke"

# Stream the response as it's generated
cllm --model gpt-4 --stream "Tell me a story"

# Read from stdin (pipe-friendly!)
echo "What is 2+2?" | cllm --model gpt-4
cat document.txt | cllm "Summarize this:"

# Control creativity with temperature
cllm --model gpt-4 --temperature 1.5 "Write a creative story"

# Limit response length
cllm --model gpt-4 --max-tokens 100 "Explain quantum computing"
```

### Conversation Threading

CLLM supports multi-turn conversations with automatic context management (ADR-0007):

```bash
# Start a new conversation with a custom ID
cllm --conversation code-review "Review this authentication code: $(cat auth.py)"

# Continue the conversation - context is automatically loaded
cllm --conversation code-review "What about SQL injection risks?"

# Continue again - full conversation history is maintained
cllm --conversation code-review "Show me how to fix these issues"

# Or let CLLM auto-generate a conversation ID
cllm --conversation conv-a3f9b2c1 "Start a discussion about Python best practices"

# List all your conversations
cllm --list-conversations

# View a conversation's full history
cllm --show-conversation code-review

# Delete a conversation when done
cllm --delete-conversation code-review
```

**Key Features:**

- **Stateless by default**: Without `--conversation`, CLLM works as before (no history saved)
- **Named conversations**: Use meaningful IDs like `bug-investigation` or `refactor-planning`
- **Auto-generated IDs**: Omit the ID to get a UUID-based identifier like `conv-a3f9b2c1`
- **Context preservation**: Full message history is maintained across calls
- **Model consistency**: The model is remembered for each conversation
- **Token tracking**: Automatic token counting to help manage context windows
- **Smart storage**: Conversations stored in `./.cllm/conversations/` (project-specific) or `~/.cllm/conversations/` (global)

**Example Workflow:**

```bash
# Start investigating a bug
cllm --conversation bug-123 "I'm seeing intermittent timeouts in production"

# Add more context as you debug
cllm --conversation bug-123 "Here are the logs: $(cat error.log)"

# Ask follow-up questions
cllm --conversation bug-123 "Could this be related to connection pooling?"

# Get the solution
cllm --conversation bug-123 "How should I fix this?"

# Review the conversation later
cllm --show-conversation bug-123
```

### Configuration

Set up API keys as environment variables (LiteLLM conventions):

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google/Gemini
export GOOGLE_API_KEY="..."

# Other providers follow similar patterns
# See: https://docs.litellm.ai/docs/providers
```

**Note**: CLLM uses [LiteLLM](https://github.com/BerriAI/litellm) for provider abstraction, supporting 100+ LLM providers with a unified interface. See [ADR-0002](docs/decisions/0002-use-litellm-for-llm-provider-abstraction.md) for details.

### Debugging & Troubleshooting

CLLM provides powerful debugging capabilities for troubleshooting API issues, understanding token usage, and investigating unexpected behavior:

```bash
# Enable debug mode (shows API calls, headers, response metadata)
cllm --debug "Explain quantum computing"
# ⚠️  Debug mode enabled. API keys may appear in output.

# Enable structured JSON logging for observability tools
cllm --json-logs "Process this data" < input.txt

# Save debug output to a file (preserves stdout for piping)
cllm --debug --log-file debug.log "Query" < data.txt

# Combine multiple debug options
cllm --debug --json-logs --log-file cllm-debug.json "Test prompt"

# Use environment variables for persistent debugging
export CLLM_DEBUG=true
export CLLM_LOG_FILE=cllm.log
cllm "What is 2+2?"  # Debug output automatically enabled
```

**Debug Output Includes:**
- Full request/response details
- API endpoint and headers
- Token usage and costs
- Latency measurements
- Error messages and stack traces

**Security Warning**: Debug mode logs API keys. Never use `--debug` in production or with confidential data.

See [ADR-0009](docs/decisions/0009-add-debugging-and-logging-support.md) for complete documentation.

### Python API

CLLM can also be used as a Python library:

```python
from cllm import LLMClient

# Initialize client
client = LLMClient()

# Simple completion
response = client.complete(
    model="gpt-4",
    messages="What is the capital of France?"
)
print(response)  # "Paris"

# Switch provider (same code!)
response = client.complete(
    model="claude-3-opus-20240229",
    messages="What is the capital of France?"
)

# Multi-turn conversation with history
conversation = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's 2+2?"}
]
response = client.complete(model="gpt-4", messages=conversation)

# Or use ConversationManager for persistent conversations
from cllm.conversation import ConversationManager

manager = ConversationManager()
conv = manager.create(conversation_id="my-chat", model="gpt-4")

# Add messages
conv.add_message("user", "Hello!")
manager.save(conv)

# Load and continue
conv = manager.load("my-chat")
conv.add_message("user", "What's 2+2?")
response = client.complete(model=conv.model, messages=conv.get_messages())
conv.add_message("assistant", response)
manager.save(conv)

# Streaming (real-time output + complete response)
response = client.complete(model="gpt-4", messages="Count to 5", stream=True)
# Output is printed in real-time, response contains complete text
print(f"\nFinal response: {response}")

# Async support
import asyncio

async def main():
    response = await client.acomplete(
        model="gpt-4",
        messages="Hello!"
    )
    print(response)

asyncio.run(main())
```

See the [`examples/`](examples/) directory for more usage patterns.

## Advanced Usage

### LLM Chaining with Bash Pipes

Chain multiple LLM calls together to build complex workflows:

```bash
# Generate a story outline, then expand it
cllm "Write a 3-point outline for a sci-fi story" | \
  cllm "Expand this outline into a full story:"

# Analyze code and generate tests
cat my_code.py | \
  cllm "Analyze this code and suggest edge cases" | \
  cllm "Generate pytest unit tests for these cases"

# Multi-stage content refinement
echo "Topic: Climate change" | \
  cllm "Create an outline" | \
  cllm "Expand with examples" | \
  cllm "Add citations"
```

### Bash Script Examples

CLLM includes a library of curated bash scripts for common workflows (see `examples/bash/`):

```bash
# Interactive prompt loop with conversation context
./examples/bash/prompt-loop.sh my-conversation

# Code review workflow for git diffs
git diff main | ./examples/bash/git-diff-review.sh

# Automated daily summaries (for cron)
./examples/bash/cron-digest.sh
```

**Key features of example scripts:**
- POSIX-compatible bash (`set -euo pipefail`)
- Robust error handling
- Environment variable configuration
- Smoke-tested in CI

See [ADR-0008](docs/decisions/0008-add-bash-script-examples.md) for implementation details.

### Structured Output with JSON Schema

Get guaranteed structured JSON output that conforms to your schema (ADR-0005):

```bash
# Using inline JSON schema
echo "John Doe, age 30, software engineer" | \
  cllm --model gpt-4o --json-schema '{
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "number"},
      "occupation": {"type": "string"}
    },
    "required": ["name", "age"]
  }'

# Using external schema file
cat document.txt | cllm --model gpt-4o --json-schema-file schemas/person.json

# Using Cllmfile configuration
echo "Extract entities..." | cllm --config extraction

# Parse output with jq
cllm --json-schema-file schemas/person.json "Extract info..." | jq '.name'

# Validate schema before using (no API call)
cllm --validate-schema --json-schema-file examples/schemas/person.json
```

**Example schemas available in `examples/schemas/`:**

- `person.json` - Extract person information
- `entity-extraction.json` - Named entity recognition
- `sentiment.json` - Sentiment analysis with emotions

**Tip:** Use `--validate-schema` to test your schemas without making API calls.

See [`examples/schemas/README.md`](examples/schemas/README.md) for detailed usage and examples.

### Configuration Files (Cllmfile.yml)

Create reusable configuration profiles to reduce repetitive CLI flags (ADR-0003):

```yaml
# Cllmfile.yml - Project-wide defaults
model: "gpt-4"
temperature: 0.7
max_tokens: 1000
timeout: 60
num_retries: 2

# Fallback models (automatic failover)
fallbacks:
  - "gpt-3.5-turbo-16k"
  - "claude-3-sonnet-20240229"

# Environment variable interpolation
api_key: "${OPENAI_API_KEY}"

# Default system message
default_system_message: "You are a helpful coding assistant."
```

**Named Configurations:**

```bash
# Create profile-specific configs
# examples/configs/summarize.Cllmfile.yml
# examples/configs/creative.Cllmfile.yml
# examples/configs/code-review.Cllmfile.yml

# Use named configurations
cat article.md | cllm --config summarize
echo "Write a story" | cllm --config creative
git diff | cllm --config code-review

# Override config with CLI args (CLI always wins)
cllm --config summarize --temperature 0.5 < doc.txt

# Debug effective configuration
cllm --show-config --config my-profile
```

**File Precedence** (lowest to highest):
1. `~/.cllm/Cllmfile.yml` (global defaults)
2. `./.cllm/Cllmfile.yml` (project-specific)
3. `./Cllmfile.yml` (current directory)
4. CLI arguments (highest priority)

See [`examples/configs/`](examples/configs/) for example configurations.

## Examples

### Code Review Pipeline

```bash
#!/bin/bash
# code_review.sh

git diff main | \
  cllm "Review this code diff and identify issues:" | \
  cllm "Suggest fixes for these issues:" | \
  cllm "Rate the severity of each issue (1-10):"
```

### Content Generation Workflow

```bash
#!/bin/bash
# content_workflow.sh

TOPIC="$1"

# Generate outline
OUTLINE=$(cllm "Create a blog post outline about: $TOPIC")

# Expand each section
echo "$OUTLINE" | \
  cllm "Expand each point into full paragraphs:" | \
  cllm "Add relevant examples and statistics:" | \
  cllm "Polish the writing and improve clarity:"
```

### Data Analysis Pipeline

```bash
#!/bin/bash
# analyze_data.sh

cat sales_data.csv | \
  cllm "Analyze this sales data and identify trends:" | \
  cllm "Suggest actionable recommendations:" | \
  cllm --json-schema-file examples/schemas/report.json > report.json
```

## CLI Reference

### Main Command

```bash
cllm [OPTIONS] [PROMPT]
```

### Key Options

| Option                         | Description                                      |
| ------------------------------ | ------------------------------------------------ |
| `--model MODEL`                | Specify LLM model (default: gpt-3.5-turbo)      |
| `--list-models`                | List all available models across providers       |
| `--stream`                     | Stream response in real-time                     |
| `--temperature FLOAT`          | Control randomness (0.0-2.0)                     |
| `--max-tokens INT`             | Maximum response length                          |
| `--conversation ID`            | Continue/create multi-turn conversation          |
| `--list-conversations`         | List all saved conversations                     |
| `--show-conversation ID`       | Display conversation history                     |
| `--delete-conversation ID`     | Delete a conversation                            |
| `--config NAME`                | Load named Cllmfile configuration                |
| `--show-config`                | Display effective configuration                  |
| `--json-schema FILE/URL`       | Enforce JSON schema for structured output        |
| `--validate-schema`            | Validate schema without making API call          |
| `--debug`                      | Enable debug mode (⚠️ logs API keys)             |
| `--json-logs`                  | Enable structured JSON logging                   |
| `--log-file PATH`              | Write debug output to file                       |
| `--help`                       | Show help message                                |

## Providers & Models

CLLM supports 100+ providers through LiteLLM. Use `cllm --list-models` to see all available models.

### Popular Providers

**OpenAI**
- `gpt-3.5-turbo` (default)
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`
- `gpt-4o-mini`

**Anthropic**
- `claude-3-haiku-20240307`
- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`
- `claude-3-5-sonnet-20240620`

**Google**
- `gemini-pro`, `gemini-1.5-pro`, `gemini-1.5-flash`

**Groq (Fast Inference)**
- `groq/mixtral-8x7b-32768`
- `groq/llama-3.1-70b-versatile`
- `groq/llama-3.3-70b-versatile`

**Ollama (Local Models)**
- `ollama/llama3`, `ollama/codellama`, `ollama/mistral`
- Any custom Ollama model

**Other Providers**
- AWS Bedrock, Azure OpenAI, Cohere, Replicate, Together AI, Hugging Face, and 90+ more

**Model Discovery:**
```bash
# List all 1343+ available models
cllm --list-models

# Filter by provider
cllm --list-models | grep -i anthropic
cllm --list-models | grep -i gpt-4
```

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for complete list and setup instructions.

## Environment Variables

### Provider API Keys

```bash
# Provider API keys (LiteLLM conventions)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export GROQ_API_KEY="gsk_..."
export AZURE_API_KEY="..."
export COHERE_API_KEY="..."
# See https://docs.litellm.ai/docs/providers for all providers
```

### CLLM Configuration

```bash
# Default model (optional)
export CLLM_DEFAULT_MODEL="gpt-4"

# Debug settings (ADR-0009)
export CLLM_DEBUG=true
export CLLM_JSON_LOGS=true
export CLLM_LOG_FILE=/path/to/debug.log
```

## Development

### Setup

```bash
git clone https://github.com/o3-cloud/cllm.git
cd cllm
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Build

```bash
uv build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ by the O3 Cloud team
- Inspired by the need for transparent, scriptable LLM workflows
- Thanks to all contributors and the open-source community

## Support

- 📖 [Documentation](https://github.com/o3-cloud/cllm/wiki)
- 🐛 [Issue Tracker](https://github.com/o3-cloud/cllm/issues)
- 💬 [Discussions](https://github.com/o3-cloud/cllm/discussions)

## Architecture Decision Records

CLLM's architecture and features are documented in ADRs (Architecture Decision Records):

- [ADR-0001](docs/decisions/0001-use-uv-as-package-manager.md): Use uv as Package Manager (10-100x faster than pip)
- [ADR-0002](docs/decisions/0002-use-litellm-for-llm-provider-abstraction.md): Use LiteLLM for Provider Abstraction (100+ providers)
- [ADR-0003](docs/decisions/0003-cllmfile-configuration-system.md): Cllmfile Configuration System (YAML configs)
- [ADR-0004](docs/decisions/0004-add-list-models-cli-flag.md): Add `--list-models` CLI Flag (model discovery)
- [ADR-0005](docs/decisions/0005-add-structured-output-support.md): Structured Output with JSON Schema
- [ADR-0006](docs/decisions/0006-support-remote-json-schema-urls.md): Support Remote JSON Schema URLs
- [ADR-0007](docs/decisions/0007-conversation-threading-and-context-management.md): Conversation Threading & Context Management
- [ADR-0008](docs/decisions/0008-add-bash-script-examples.md): Bash Script Examples Library
- [ADR-0009](docs/decisions/0009-add-debugging-and-logging-support.md): Debugging & Logging Support
- [ADR-0010](docs/decisions/0010-implement-litellm-streaming-support.md): LiteLLM Streaming Support

## Roadmap

**Completed:**
- ✅ Multi-provider support (100+ providers)
- ✅ Real-time streaming responses
- ✅ Conversation threading
- ✅ Structured JSON output with schema validation
- ✅ Configuration file system
- ✅ Debugging and logging
- ✅ Model discovery
- ✅ Bash script examples

**Planned:**
- [ ] Enhanced error recovery and retry strategies
- [ ] Token usage tracking and cost estimation
- [ ] Built-in prompt templates library
- [ ] Prompt caching support
- [ ] Function calling / tool use
- [ ] Multimodal support (images, audio)
- [ ] Plugin system for extensibility
- [ ] Integration with popular dev tools (VSCode, Emacs)

---

**Star ⭐ this repository if you find it useful!**
