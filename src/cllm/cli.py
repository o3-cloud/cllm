"""
Command-line interface for CLLM.

Provides a bash-centric CLI for interacting with LLMs across multiple providers.
"""

import argparse
import sys
from typing import Optional

from .client import LLMClient


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


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Read prompt
    prompt = read_prompt(args.prompt)

    # Initialize client
    client = LLMClient()

    # Prepare parameters
    kwargs = {}
    if args.temperature is not None:
        kwargs["temperature"] = args.temperature
    if args.max_tokens is not None:
        kwargs["max_tokens"] = args.max_tokens
    if args.raw:
        kwargs["raw_response"] = True

    try:
        # Make the request
        if args.stream:
            # Streaming mode
            for chunk in client.complete(
                model=args.model, messages=prompt, stream=True, **kwargs
            ):
                print(chunk, end="", flush=True)
            print()  # Final newline
        else:
            # Non-streaming mode
            response = client.complete(model=args.model, messages=prompt, **kwargs)

            if args.raw:
                import json

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
