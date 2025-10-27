"""
Command-line interface for CLLM.

Provides a bash-centric CLI for interacting with LLMs across multiple providers.
"""

import argparse
import json
import sys
from typing import Optional

import litellm

from .client import LLMClient
from .config import ConfigurationError, get_config_sources, load_config, merge_config_with_args


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="cllm",
        description="Command-line interface for interacting with large language models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple completion with OpenAI
  cllm "What is the capital of France?" --model gpt-4

  # Use a different provider (Anthropic)
  cllm "Explain APIs briefly" --model claude-3-opus-20240229

  # Streaming response
  cllm "Tell me a story" --model gpt-4 --stream

  # Read from stdin
  echo "What is 2+2?" | cllm --model gpt-4

  # Control creativity with temperature
  cllm "Write a creative story" --model gpt-4 --temperature 1.5

  # Limit response length
  cllm "Explain quantum computing" --model gpt-4 --max-tokens 100

Supported Providers (partial list):
  - OpenAI: gpt-4, gpt-3.5-turbo
  - Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229
  - Google: gemini-pro
  - And 100+ more via LiteLLM

For full provider list: https://docs.litellm.ai/docs/providers
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="The prompt to send to the LLM (reads from stdin if not provided)",
    )

    parser.add_argument(
        "-m",
        "--model",
        default="gpt-3.5-turbo",
        help="Model to use (default: gpt-3.5-turbo)",
    )

    parser.add_argument(
        "-t", "--temperature", type=float, help="Sampling temperature (0.0 to 2.0)"
    )

    parser.add_argument("--max-tokens", type=int, help="Maximum tokens to generate")

    parser.add_argument(
        "-s",
        "--stream",
        action="store_true",
        help="Stream the response as it's generated",
    )

    parser.add_argument("--raw", action="store_true", help="Output raw JSON response")

    parser.add_argument(
        "-c",
        "--config",
        metavar="NAME",
        help="Use named configuration file (e.g., 'summarize' loads summarize.Cllmfile.yml)",
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display effective configuration and exit",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all available models and exit",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser


def read_prompt(prompt_arg: Optional[str]) -> str:
    """
    Read the prompt from argument or stdin.

    Args:
        prompt_arg: The prompt from command line arguments

    Returns:
        The prompt text
    """
    if prompt_arg:
        return prompt_arg

    # Read from stdin
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    # No prompt provided
    print("Error: No prompt provided. Use 'cllm --help' for usage.", file=sys.stderr)
    sys.exit(1)


def print_model_list():
    """
    Print a list of all available models from LiteLLM.

    Models are organized by provider for better readability while
    maintaining bash-friendly formatting (grep-able, one model per line).
    """
    # Get all models from LiteLLM
    models = sorted(litellm.model_list)

    # Define common provider prefixes and their display names
    provider_prefixes = {
        'openai/': 'OpenAI',
        'anthropic/': 'Anthropic',
        'claude-': 'Anthropic',
        'gpt-': 'OpenAI',
        'google/': 'Google',
        'gemini': 'Google',
        'azure/': 'Azure',
        'bedrock/': 'AWS Bedrock',
        'cohere/': 'Cohere',
        'command-': 'Cohere',
        'replicate/': 'Replicate',
        'huggingface/': 'HuggingFace',
        'together_ai/': 'Together AI',
        'palm/': 'Google PaLM',
        'openrouter/': 'OpenRouter',
        'vertex_ai/': 'Vertex AI',
        'groq/': 'Groq',
        'mistral/': 'Mistral',
        'deepseek': 'DeepSeek',
        'databricks/': 'Databricks',
        'ollama/': 'Ollama',
    }

    # Categorize models by provider
    categorized = {}
    uncategorized = []

    for model in models:
        matched = False
        for prefix, provider_name in provider_prefixes.items():
            if model.startswith(prefix) or (prefix.endswith('-') and prefix.rstrip('-') in model):
                if provider_name not in categorized:
                    categorized[provider_name] = []
                categorized[provider_name].append(model)
                matched = True
                break

        if not matched:
            uncategorized.append(model)

    # Print header
    print(f"Available Models ({len(models)} total)")
    print("=" * 60)
    print()

    # Print categorized models
    for provider in sorted(categorized.keys()):
        print(f"{provider}:")
        for model in categorized[provider]:
            print(f"  {model}")
        print()

    # Print uncategorized models
    if uncategorized:
        print("Other Providers:")
        for model in uncategorized:
            print(f"  {model}")
        print()

    # Print usage hint
    print("=" * 60)
    print("Tip: Use grep to filter models, e.g., 'cllm --list-models | grep gpt'")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load configuration from files
        file_config = load_config(config_name=args.config)
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Build CLI args dict (only non-None values)
    cli_args = {}
    if args.model and args.model != "gpt-3.5-turbo":  # Only if explicitly set
        cli_args["model"] = args.model
    if args.temperature is not None:
        cli_args["temperature"] = args.temperature
    if args.max_tokens is not None:
        cli_args["max_tokens"] = args.max_tokens
    if args.stream:
        cli_args["stream"] = args.stream
    if args.raw:
        cli_args["raw_response"] = args.raw

    # Merge config with CLI args (CLI takes precedence)
    config = merge_config_with_args(file_config, cli_args)

    # Set defaults if not in config
    if "model" not in config:
        config["model"] = "gpt-3.5-turbo"

    # Handle --show-config
    if args.show_config:
        sources = get_config_sources(config_name=args.config)
        print("Configuration sources (in order of precedence):")
        if sources:
            for source in sources:
                print(f"  - {source}")
        else:
            print("  (no configuration files found)")
        print("\nEffective configuration:")
        print(json.dumps(config, indent=2))
        sys.exit(0)

    # Handle --list-models
    if args.list_models:
        print_model_list()
        sys.exit(0)

    # Read prompt (not needed for --show-config or --list-models)
    prompt = read_prompt(args.prompt)

    # Initialize client
    client = LLMClient()

    # Extract parameters for LLM call
    model = config.get("model", "gpt-3.5-turbo")
    stream = config.get("stream", False)
    raw_response = config.get("raw_response", False)

    # Prepare kwargs for client.complete()
    # Pass through all LiteLLM parameters from config
    kwargs = {
        k: v
        for k, v in config.items()
        if k not in ["model", "stream", "raw_response", "default_system_message"]
    }

    # Handle default_system_message if present
    if "default_system_message" in config:
        # Prepend system message to prompt
        system_msg = config["default_system_message"]
        prompt = f"{system_msg}\n\n{prompt}"

    if raw_response:
        kwargs["raw_response"] = True

    try:
        # Make the request
        if stream:
            # Streaming mode
            for chunk in client.complete(
                model=model, messages=prompt, stream=True, **kwargs
            ):
                print(chunk, end="", flush=True)
            print()  # Final newline
        else:
            # Non-streaming mode
            response = client.complete(model=model, messages=prompt, **kwargs)

            if raw_response:
                print(json.dumps(response, indent=2))
            else:
                print(response)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
