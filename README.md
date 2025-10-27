# CLLM - Command Line LLM Toolkit

A bash-centric command-line interface for interacting with large language models. Chain LLM inference processes using familiar bash piping and scripting techniques.

## Overview

CLLM bridges the gap between ChatGPT GUIs, prompt libraries, notebooks, and agent frameworks by providing transparency and bash integration for complex AI workflows. It's designed for developers who want programmatic control over LLM interactions without leaving their terminal.

## Features

- **🚀 Simple CLI Interface**: Generate text from prompts with straightforward commands
- **🔗 LLM Chaining**: Chain multiple LLM calls using bash pipes and scripts
- **📋 Structured Output**: Get guaranteed JSON output conforming to JSON Schema specifications
- **🏢 Multi-Provider Support**:
  - OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo)
  - Anthropic (Claude 3 Family)
  - Google Gemini
  - Groq
  - AWS Bedrock
  - Local Ollama models
- **🛠️ Utility Suite**:
  - Vector stores for semantic search
  - Text splitters for document processing
  - Data loaders for various file formats
  - Output parsers for structured responses
- **🐳 Docker Support**: Run in containerized environments
- **⚙️ Flexible Configuration**: Easy setup through `.cllm` directory structure and Cllmfile.yml

## Requirements

- Python 3.8 or higher
- API keys for your chosen LLM provider(s)
- uv (for development and package management)

## Installation

### Via pip (recommended)

```bash
pip install cllm
```

### From source

```bash
git clone https://github.com/o3-cloud/cllm.git
cd cllm
uv sync
```

### Docker

```bash
docker pull o3cloud/cllm:latest
docker run -it o3cloud/cllm:latest
```

## Quick Start

### Basic Usage

```bash
# Simple prompt (uses gpt-3.5-turbo by default)
cllm "What is the capital of France?"

# Use a specific model
cllm --model gpt-4 "Explain quantum computing"

# Use a different provider (same interface!)
cllm --model claude-3-opus-20240229 "Write a haiku"
cllm --model gemini-pro "Tell me a joke"

# Stream the response as it's generated
cllm --model gpt-4 --stream "Tell me a story"

# Read from stdin (pipe-friendly!)
echo "What is 2+2?" | cllm --model gpt-4

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
response = client.chat(model="gpt-4", messages=conversation)

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

# Streaming
for chunk in client.complete(model="gpt-4", messages="Count to 5", stream=True):
    print(chunk, end="", flush=True)

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

### LLM Chaining

Chain multiple LLM calls together:

```bash
# Generate a story outline, then expand it
cllm "Write a 3-point outline for a sci-fi story" | \
  cllm "Expand this outline into a full story:"

# Analyze code and generate tests
cat my_code.py | \
  cllm "Analyze this code and suggest edge cases" | \
  cllm "Generate pytest unit tests for these cases"
```

### Using Vector Stores

```bash
# Index documents
cllm-index --directory ./docs --output ./docs.db

# Query the vector store
cllm-query --db ./docs.db "How do I configure authentication?"
```

### Text Splitting

```bash
# Split a large document for processing
cllm-split --input large_doc.txt --chunk-size 1000 --output chunks/

# Process each chunk
for chunk in chunks/*.txt; do
  cat "$chunk" | cllm "Summarize this text:" >> summaries.txt
done
```

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
  cllm --format json "Convert to structured report:" > report.json
```

## Commands

| Command       | Description                        |
| ------------- | ---------------------------------- |
| `cllm`        | Main CLI for LLM interactions      |
| `cllm-index`  | Index documents into vector stores |
| `cllm-query`  | Query vector stores                |
| `cllm-split`  | Split text into chunks             |
| `cllm-config` | Manage configuration               |
| `cllm-models` | List available models              |

## Providers & Models

### OpenAI

- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`

### Anthropic

- `claude-3-haiku`
- `claude-3-sonnet`
- `claude-3-opus`
- `claude-3-5-sonnet`

### Google

- `gemini-pro`
- `gemini-1.5-pro`
- `gemini-1.5-flash`

### Groq

- `mixtral-8x7b`
- `llama-3-70b`

### Ollama (Local)

- `llama3`
- `codellama`
- `mistral`
- Custom models

## Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export GROQ_API_KEY="gsk_..."
export CLLM_DEFAULT_PROVIDER="openai"
export CLLM_DEFAULT_MODEL="gpt-4-turbo"
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

## Roadmap

- [ ] Support for more LLM providers
- [ ] Enhanced vector store capabilities
- [ ] Built-in prompt templates
- [ ] Streaming support for real-time responses
- [ ] Plugin system for extensibility
- [ ] Web UI for configuration management
- [ ] Integration with popular dev tools

---

**Star ⭐ this repository if you find it useful!**
