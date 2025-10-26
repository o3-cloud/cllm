# CLLM Examples

This directory contains example scripts demonstrating how to use CLLM with different LLM providers.

## Prerequisites

1. Install CLLM:

   ```bash
   uv pip install -e .
   ```

2. Set up API keys as environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GOOGLE_API_KEY="your-google-key"
   # ... other providers as needed
   ```

## Examples

### basic_usage.py

Demonstrates basic usage patterns including:

- Simple completions with different providers
- Multi-turn conversations
- Streaming responses
- Temperature control

```bash
python examples/basic_usage.py
```

### async_usage.py

Shows how to use async/await for concurrent queries to multiple providers.

```bash
python examples/async_usage.py
```

### provider_comparison.py

Compares responses from different providers to the same prompt, demonstrating how easy it is to switch providers.

```bash
python examples/provider_comparison.py
```

## Key Concepts

### Switching Providers

The main benefit of LiteLLM is that you use the same code for all providers:

```python
from cllm import LLMClient

client = LLMClient()

# OpenAI
response = client.complete("gpt-4", "Hello!")

# Anthropic - same code!
response = client.complete("claude-3-opus-20240229", "Hello!")

# Google - same code!
response = client.complete("gemini-pro", "Hello!")
```

### Model Names

LiteLLM uses provider-specific model names:

- OpenAI: `gpt-4`, `gpt-3.5-turbo`, etc.
- Anthropic: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, etc.
- Google: `gemini-pro`, `gemini-pro-vision`, etc.
- And 100+ more providers

See the full list: https://docs.litellm.ai/docs/providers

## Notes

- Examples will only work for providers where you have valid API keys configured
- Errors for providers without keys are expected and handled gracefully
- All examples use the same `LLMClient` interface, demonstrating ADR-0002
