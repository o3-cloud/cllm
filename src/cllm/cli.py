"""
Command-line interface for CLLM.

Provides a bash-centric CLI for interacting with LLMs across multiple providers.
Implements ADR-0005: Add Structured Output Support with JSON Schema
"""

import argparse
import json
import sys
from typing import Dict, Optional, Any

import litellm

from .client import LLMClient
from .config import (
    ConfigurationError,
    get_config_sources,
    load_config,
    load_json_schema,
    merge_config_with_args,
    validate_against_schema,
)


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

    parser.add_argument(
        "--json-schema",
        metavar="SCHEMA",
        help="JSON schema for structured output (inline JSON string)",
    )

    parser.add_argument(
        "--json-schema-file",
        metavar="FILE",
        help="Path to JSON schema file for structured output",
    )

    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate the JSON schema and exit (no LLM call made)",
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
    if args.json_schema is not None:
        cli_args["json_schema"] = args.json_schema
    if args.json_schema_file is not None:
        cli_args["json_schema_file"] = args.json_schema_file

    # Merge config with CLI args (CLI takes precedence)
    config = merge_config_with_args(file_config, cli_args)

    # Set defaults if not in config
    if "model" not in config:
        config["model"] = "gpt-3.5-turbo"

    # Handle JSON schema with proper precedence
    # Precedence: --json-schema > --json-schema-file > json_schema in config > json_schema_file in config
    schema: Optional[Dict[str, Any]] = None
    try:
        if "json_schema" in config and isinstance(config["json_schema"], str):
            # CLI flag --json-schema (inline JSON string)
            schema = load_json_schema(json.loads(config["json_schema"]))
        elif "json_schema" in config and isinstance(config["json_schema"], dict):
            # Cllmfile inline schema (already parsed from YAML)
            schema = load_json_schema(config["json_schema"])
        elif "json_schema_file" in config:
            # CLI flag --json-schema-file or Cllmfile json_schema_file
            schema = load_json_schema(config["json_schema_file"])
    except (json.JSONDecodeError, ConfigurationError) as e:
        print(f"Schema error: {e}", file=sys.stderr)
        sys.exit(1)

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

    # Handle --validate-schema
    if args.validate_schema:
        if schema is None:
            print("Error: No schema provided. Use --json-schema or --json-schema-file", file=sys.stderr)
            sys.exit(1)

        print("✓ Schema is valid!")
        print("\nSchema details:")
        print(f"  Type: {schema.get('type', 'not specified')}")

        if schema.get('type') == 'object':
            props = schema.get('properties', {})
            print(f"  Properties: {len(props)}")
            if props:
                print("  Fields:")
                for prop_name, prop_schema in props.items():
                    prop_type = prop_schema.get('type', 'any')
                    required = '(required)' if prop_name in schema.get('required', []) else '(optional)'
                    print(f"    - {prop_name}: {prop_type} {required}")
        elif schema.get('type') == 'array':
            items = schema.get('items', {})
            print(f"  Items type: {items.get('type', 'any')}")

        print(f"\n✓ Schema validation successful")
        sys.exit(0)

    # Read prompt (not needed for --show-config, --list-models, or --validate-schema)
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
        if k not in ["model", "stream", "raw_response", "default_system_message", "json_schema", "json_schema_file"]
    }

    # Handle default_system_message if present
    if "default_system_message" in config:
        # Prepend system message to prompt
        system_msg = config["default_system_message"]
        prompt = f"{system_msg}\n\n{prompt}"

    # Add response_format for structured output if schema is present
    if schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response_schema",
                "schema": schema,
            }
        }

    if raw_response:
        kwargs["raw_response"] = True

    try:
        # Make the request
        if stream:
            # Streaming mode
            if schema is not None:
                # For streaming with schema, we need to collect all chunks first
                # to validate the complete response
                chunks = []
                for chunk in client.complete(
                    model=model, messages=prompt, stream=True, **kwargs
                ):
                    chunks.append(chunk)
                    print(chunk, end="", flush=True)
                print()  # Final newline

                # Validate the complete response
                complete_response = "".join(chunks)
                try:
                    parsed_response = json.loads(complete_response)
                    validate_against_schema(parsed_response, schema)
                except json.JSONDecodeError as e:
                    print(f"\nWarning: Response is not valid JSON: {e}", file=sys.stderr)
                    sys.exit(1)
                except ConfigurationError as e:
                    print(f"\nValidation error: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                # Normal streaming without schema
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
                # Validate against schema if present
                if schema is not None:
                    try:
                        parsed_response = json.loads(response)
                        validate_against_schema(parsed_response, schema)
                    except json.JSONDecodeError as e:
                        print(f"Error: Response is not valid JSON: {e}", file=sys.stderr)
                        print(f"Response: {response}", file=sys.stderr)
                        sys.exit(1)
                    except ConfigurationError as e:
                        print(f"Validation error: {e}", file=sys.stderr)
                        print(f"Response: {response}", file=sys.stderr)
                        sys.exit(1)

                print(response)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
