# CLLM - Command Line LLM Toolkit

A bash-centric command-line interface for interacting with large language models. Chain LLM inference processes using familiar bash piping and scripting techniques.

## Overview

CLLM bridges the gap between ChatGPT GUIs, prompt libraries, notebooks, and agent frameworks by providing transparency and bash integration for complex AI workflows. It's designed for developers who want programmatic control over LLM interactions without leaving their terminal.

## Features

- **🚀 Simple CLI Interface**: Generate text from prompts with straightforward commands
- **🔗 LLM Chaining**: Chain multiple LLM calls using bash pipes and scripts
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
- **⚙️ Flexible Configuration**: Easy setup through `.cllm` directory structure

## Requirements

- Python 3.8 or higher
- API keys for your chosen LLM provider(s)
- Poetry (for development)

## Installation

### Via pip (recommended)

```bash
pip install cllm
```

### From source

```bash
git clone https://github.com/o3-cloud/cllm.git
cd cllm
poetry install
```

### Docker

```bash
docker pull o3cloud/cllm:latest
docker run -it o3cloud/cllm:latest
```

## Quick Start

### Basic Usage

```bash
# Simple prompt
cllm "What is the capital of France?"

# Use a specific model
cllm --model gpt-4 "Explain quantum computing"

# Use a different provider
cllm --provider anthropic --model claude-3-sonnet "Write a haiku"
```

### Configuration

Create a `.cllm` directory in your home or project directory:

```bash
mkdir -p ~/.cllm
```

Add your API keys to `~/.cllm/config.json`:

```json
{
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-...",
  "google_api_key": "...",
  "groq_api_key": "gsk_...",
  "default_provider": "openai",
  "default_model": "gpt-4-turbo"
}
```

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

### Output Parsing

```bash
# Get structured JSON output
cllm --format json "List the top 5 programming languages with their use cases"

# Parse and process
cllm --format json "Analyze this data" < data.csv | jq '.recommendations'
```

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

| Command | Description |
|---------|-------------|
| `cllm` | Main CLI for LLM interactions |
| `cllm-index` | Index documents into vector stores |
| `cllm-query` | Query vector stores |
| `cllm-split` | Split text into chunks |
| `cllm-config` | Manage configuration |
| `cllm-models` | List available models |

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
poetry install
poetry shell
```

### Run Tests

```bash
poetry run pytest
```

### Build

```bash
poetry build
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
