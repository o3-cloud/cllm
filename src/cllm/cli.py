"""
Command-line interface for CLLM.

Provides a bash-centric CLI for interacting with LLMs across multiple providers.
Implements ADR-0005: Add Structured Output Support with JSON Schema
Implements ADR-0009: Add Debugging and Logging Support
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import litellm

from .client import LLMClient
from .config import (
    ConfigurationError,
    clear_schema_cache,
    get_config_sources,
    load_config,
    load_json_schema,
    merge_config_with_args,
    validate_against_schema,
)
from .context import (
    ContextCommand,
    FailureMode,
    inject_context,
    parse_context_commands,
)
from .conversation import Conversation, ConversationManager
from .templates import TemplateError, build_template_context


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

    parser.add_argument(
        "--clear-schema-cache",
        action="store_true",
        help="Clear all cached remote schemas and exit",
    )

    # Conversation management arguments
    parser.add_argument(
        "--conversation",
        metavar="ID",
        help="Use or create conversation with specified ID (auto-generates if ID not provided)",
    )

    parser.add_argument(
        "--list-conversations",
        action="store_true",
        help="List all stored conversations and exit",
    )

    parser.add_argument(
        "--show-conversation",
        metavar="ID",
        help="Display conversation contents and exit",
    )

    parser.add_argument(
        "--delete-conversation",
        metavar="ID",
        help="Delete conversation and exit",
    )

    # Debugging and logging arguments (ADR-0009)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logging) - ⚠️  Logs API keys - NOT for production",
    )

    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Enable JSON structured logging",
    )

    parser.add_argument(
        "--log-file",
        metavar="PATH",
        help="Write debug/log output to file instead of stderr",
    )

    # Context injection arguments (ADR-0011)
    parser.add_argument(
        "--exec",
        action="append",
        metavar="COMMAND",
        dest="context_exec",
        help="Execute command and inject output into context (can be used multiple times)",
    )

    parser.add_argument(
        "--no-context-exec",
        action="store_true",
        help="Disable context commands from configuration file",
    )

    # Variable expansion arguments (ADR-0012)
    parser.add_argument(
        "--var",
        "-v",
        action="append",
        metavar="KEY=VALUE",
        dest="variables",
        help="Set template variable (e.g., --var FILE_PATH=src/main.py). Can be used multiple times.",
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
    stdin_content = ""

    # Read from stdin if available
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()

    # Combine prompt_arg and stdin if both exist
    if prompt_arg and stdin_content:
        return f"{prompt_arg}\n{stdin_content}"
    elif prompt_arg:
        return prompt_arg
    elif stdin_content:
        return stdin_content

    # No prompt provided
    print("Error: No prompt provided. Use 'cllm --help' for usage.", file=sys.stderr)
    sys.exit(1)


def parse_variables(var_list: Optional[list[str]]) -> Dict[str, Any]:
    """
    Parse --var KEY=VALUE arguments into a dictionary.

    Implements ADR-0012: Variable Expansion in Context Commands

    Args:
        var_list: List of "KEY=VALUE" strings from --var arguments

    Returns:
        Dictionary of parsed variables

    Raises:
        SystemExit: If variable format is invalid
    """
    if not var_list:
        return {}

    variables = {}
    for var_str in var_list:
        if "=" not in var_str:
            print(
                f"Error: Invalid variable format '{var_str}'. "
                f"Expected KEY=VALUE (e.g., --var FILE_PATH=src/main.py)",
                file=sys.stderr,
            )
            sys.exit(1)

        key, value = var_str.split("=", 1)  # Split on first '=' only

        # Validate variable name (must match [A-Za-z_][A-Za-z0-9_]*)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            print(
                f"Error: Invalid variable name '{key}'. "
                f"Variable names must start with a letter or underscore "
                f"and contain only letters, numbers, and underscores.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Try to parse value as boolean or number for convenience
        # "true"/"false" -> bool, numeric strings -> int/float, else -> str
        if value.lower() == "true":
            variables[key] = True
        elif value.lower() == "false":
            variables[key] = False
        elif value.isdigit():
            variables[key] = int(value)
        elif value.replace(".", "", 1).replace("-", "", 1).isdigit():
            # Check if it's a float
            try:
                variables[key] = float(value)
            except ValueError:
                variables[key] = value
        else:
            variables[key] = value

    return variables


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
        "openai/": "OpenAI",
        "anthropic/": "Anthropic",
        "claude-": "Anthropic",
        "gpt-": "OpenAI",
        "google/": "Google",
        "gemini": "Google",
        "azure/": "Azure",
        "bedrock/": "AWS Bedrock",
        "cohere/": "Cohere",
        "command-": "Cohere",
        "replicate/": "Replicate",
        "huggingface/": "HuggingFace",
        "together_ai/": "Together AI",
        "palm/": "Google PaLM",
        "openrouter/": "OpenRouter",
        "vertex_ai/": "Vertex AI",
        "groq/": "Groq",
        "mistral/": "Mistral",
        "deepseek": "DeepSeek",
        "databricks/": "Databricks",
        "ollama/": "Ollama",
    }

    # Categorize models by provider
    categorized = {}
    uncategorized = []

    for model in models:
        matched = False
        for prefix, provider_name in provider_prefixes.items():
            if model.startswith(prefix) or (
                prefix.endswith("-") and prefix.rstrip("-") in model
            ):
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


def print_conversation_list(manager: ConversationManager):
    """
    Print a list of all conversations.

    Args:
        manager: ConversationManager instance
    """
    conversations = manager.list_conversations()

    if not conversations:
        print("No conversations found.")
        print(
            "\nTip: Create a conversation with 'cllm --conversation <id> \"your prompt\"'"
        )
        return

    print(f"Conversations ({len(conversations)} total)")
    print("=" * 80)
    print()

    for conv in conversations:
        print(f"ID: {conv['id']}")
        print(f"  Model: {conv['model']}")
        print(f"  Messages: {conv['message_count']}")
        print(f"  Updated: {conv['updated_at']}")
        print()


def print_conversation(manager: ConversationManager, conversation_id: str):
    """
    Print the contents of a conversation.

    Args:
        manager: ConversationManager instance
        conversation_id: ID of conversation to display
    """
    try:
        conv = manager.load(conversation_id)
        print(f"Conversation: {conv.id}")
        print(f"Model: {conv.model}")
        print(f"Created: {conv.created_at}")
        print(f"Updated: {conv.updated_at}")
        print(f"Messages: {len(conv.messages)}")
        if conv.total_tokens > 0:
            print(f"Total tokens: {conv.total_tokens}")
        print("=" * 80)
        print()

        for i, msg in enumerate(conv.messages, 1):
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            print(f"[{i}] {role}:")
            print(content)
            print()

    except FileNotFoundError:
        print(f"Error: Conversation '{conversation_id}' not found", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def delete_conversation(manager: ConversationManager, conversation_id: str):
    """
    Delete a conversation.

    Args:
        manager: ConversationManager instance
        conversation_id: ID of conversation to delete
    """
    try:
        manager.delete(conversation_id)
        print(f"Deleted conversation: {conversation_id}")
    except FileNotFoundError:
        print(f"Error: Conversation '{conversation_id}' not found", file=sys.stderr)
        sys.exit(1)


def configure_debugging(
    debug: bool = False,
    json_logs: bool = False,
    log_file: Optional[str] = None,
) -> Optional[object]:
    """
    Configure LiteLLM debugging and logging.

    Implements ADR-0009: Add Debugging and Logging Support

    Args:
        debug: Enable verbose debug mode (sets litellm.set_verbose=True)
        json_logs: Enable JSON structured logging (sets litellm.json_logs=True)
        log_file: Optional path to log file (redirects stderr if provided)

    Returns:
        File handle if log_file is provided, None otherwise

    Side effects:
        - Sets litellm.set_verbose if debug=True
        - Sets litellm.json_logs if json_logs=True
        - Redirects stderr to log file if log_file is provided
        - Prints warning to stderr if debug=True
    """
    log_file_handle = None

    # Handle log file redirection first (before any output)
    if log_file:
        try:
            log_path = Path(log_file)
            # Create parent directories if needed
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Open file with restrictive permissions (0600)
            # Open in append mode to allow multiple commands to write to same file
            log_file_handle = open(log_path, "a")
            # Set restrictive permissions on Unix-like systems
            if hasattr(os, "chmod"):
                os.chmod(log_path, 0o600)
            # Redirect stderr to log file
            sys.stderr = log_file_handle
        except OSError as e:
            print(f"Error: Cannot open log file '{log_file}': {e}", file=sys.stderr)
            sys.exit(1)

    # Show warning if debug mode is enabled
    if debug:
        print(
            "⚠️  Debug mode enabled. API keys and sensitive data may appear in output.",
            file=sys.stderr,
        )
        print(
            "⚠️  Do NOT use debug mode in production or with confidential data.",
            file=sys.stderr,
        )
        print(file=sys.stderr)  # Blank line for readability

    # Configure LiteLLM debugging
    if debug:
        litellm.set_verbose = True

    if json_logs:
        litellm.json_logs = True

    return log_file_handle


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
    # Debug flags (ADR-0009)
    if args.debug:
        cli_args["debug"] = args.debug
    if args.json_logs:
        cli_args["json_logs"] = args.json_logs
    if args.log_file is not None:
        cli_args["log_file"] = args.log_file

    # Merge config with CLI args (CLI takes precedence)
    config = merge_config_with_args(file_config, cli_args)

    # Support environment variables for debug settings (ADR-0009)
    # Precedence: CLI flags > Cllmfile > Environment variables
    if "debug" not in config and os.getenv("CLLM_DEBUG") == "1":
        config["debug"] = True
    if "json_logs" not in config and os.getenv("CLLM_JSON_LOGS") == "1":
        config["json_logs"] = True
    if "log_file" not in config and os.getenv("CLLM_LOG_FILE"):
        config["log_file"] = os.getenv("CLLM_LOG_FILE")

    # Set defaults if not in config
    if "model" not in config:
        config["model"] = "gpt-3.5-turbo"

    # Configure debugging and logging (ADR-0009)
    # Do this early so debug output is captured for all operations
    log_file_handle = configure_debugging(
        debug=config.get("debug", False),
        json_logs=config.get("json_logs", False),
        log_file=config.get("log_file"),
    )

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

    # Initialize conversation manager (needed for conversation commands)
    conversation_manager = ConversationManager()

    # Handle --list-conversations
    if args.list_conversations:
        print_conversation_list(conversation_manager)
        sys.exit(0)

    # Handle --show-conversation
    if args.show_conversation:
        print_conversation(conversation_manager, args.show_conversation)
        sys.exit(0)

    # Handle --delete-conversation
    if args.delete_conversation:
        delete_conversation(conversation_manager, args.delete_conversation)
        sys.exit(0)

    # Build template context for variable expansion (ADR-0012)
    cli_vars = parse_variables(args.variables)

    raw_config_vars = config.get("variables")
    if raw_config_vars is None:
        config_vars = {}
    elif isinstance(raw_config_vars, dict):
        config_vars = raw_config_vars
    else:
        print(
            "Error: 'variables' section in configuration must be a mapping of variable names to defaults.",
            file=sys.stderr,
        )
        sys.exit(1)

    if "variables" in config:
        config["variables"] = config_vars

    env_vars = {
        var_name: os.environ[var_name]
        for var_name in config_vars
        if var_name in os.environ
    }

    try:
        template_context = build_template_context(cli_vars, config_vars, env_vars)
    except TemplateError as e:
        print(f"Variable error: {e}", file=sys.stderr)
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
        print("\nResolved variables:")
        if template_context:
            print(json.dumps(template_context, indent=2, sort_keys=True))
        else:
            print("  (no variables defined)")
        sys.exit(0)

    # Handle --list-models
    if args.list_models:
        print_model_list()
        sys.exit(0)

    # Handle --clear-schema-cache
    if args.clear_schema_cache:
        count = clear_schema_cache()
        if count > 0:
            print(f"Cleared {count} cached schema(s)")
        else:
            print("No cached schemas found")
        sys.exit(0)

    # Handle --validate-schema
    if args.validate_schema:
        if schema is None:
            print(
                "Error: No schema provided. Use --json-schema or --json-schema-file",
                file=sys.stderr,
            )
            sys.exit(1)

        print("✓ Schema is valid!")
        print("\nSchema details:")
        print(f"  Type: {schema.get('type', 'not specified')}")

        if schema.get("type") == "object":
            props = schema.get("properties", {})
            print(f"  Properties: {len(props)}")
            if props:
                print("  Fields:")
                for prop_name, prop_schema in props.items():
                    prop_type = prop_schema.get("type", "any")
                    required = (
                        "(required)"
                        if prop_name in schema.get("required", [])
                        else "(optional)"
                    )
                    print(f"    - {prop_name}: {prop_type} {required}")
        elif schema.get("type") == "array":
            items = schema.get("items", {})
            print(f"  Items type: {items.get('type', 'any')}")

        print("\n✓ Schema validation successful")
        sys.exit(0)

    # Read prompt (not needed for --show-config, --list-models, or --validate-schema)
    prompt = read_prompt(args.prompt)

    # Handle context injection (ADR-0011)
    context_commands = []

    # Parse context_commands from config (if not disabled)
    if not args.no_context_exec:
        try:
            context_commands = parse_context_commands(config)
        except ValueError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)

    # Add CLI --exec commands (these run after config commands)
    if args.context_exec:
        for i, cmd_str in enumerate(args.context_exec):
            # Create ContextCommand from CLI string
            # Use generic naming: "Command 1", "Command 2", etc.
            cli_cmd = ContextCommand(
                name=f"CLI Command {i+1}",
                command=cmd_str,
                on_failure=FailureMode.WARN,  # Default to warn for CLI commands
                timeout=10,
            )
            context_commands.append(cli_cmd)

    # Inject context if we have any commands
    if context_commands:
        try:
            prompt = inject_context(
                prompt=prompt,
                commands=context_commands,
                cwd=Path.cwd(),
                parallel=True,
                template_context=template_context,  # Pass template context for variable expansion
            )
        except RuntimeError as e:
            # This happens when a command with on_failure=FAIL fails
            print(f"Context error: {e}", file=sys.stderr)
            sys.exit(1)
        except TemplateError as e:
            # Template rendering errors
            print(f"Template error: {e}", file=sys.stderr)
            sys.exit(1)

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
        if k
        not in [
            "model",
            "stream",
            "raw_response",
            "default_system_message",
            "json_schema",
            "json_schema_file",
            "context_commands",  # ADR-0011: context injection config
            "variables",  # ADR-0012: variable expansion config
            "debug",  # ADR-0009: debug mode config
            "json_logs",  # ADR-0009: JSON logging config
            "log_file",  # ADR-0009: log file config
        ]
    }

    # Handle conversation mode
    conversation: Optional[Conversation] = None
    messages_for_llm = None

    if args.conversation:
        # Load existing conversation or create new one
        try:
            if conversation_manager.exists(args.conversation):
                conversation = conversation_manager.load(args.conversation)
                # Ensure model matches if conversation has a model set
                if conversation.model and conversation.model != model:
                    print(
                        f"Warning: Conversation uses model '{conversation.model}', "
                        f"but you specified '{model}'. Using '{conversation.model}'.",
                        file=sys.stderr,
                    )
                    model = conversation.model
            else:
                # Create new conversation
                conversation = conversation_manager.create(
                    conversation_id=args.conversation, model=model
                )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Build messages list with conversation history
        messages_for_llm = conversation.get_messages().copy()

        # Handle default_system_message if present and conversation is new
        if "default_system_message" in config and len(messages_for_llm) == 0:
            messages_for_llm.append(
                {"role": "system", "content": config["default_system_message"]}
            )

        # Add new user message
        messages_for_llm.append({"role": "user", "content": prompt})

    else:
        # Stateless mode - use prompt directly
        # Handle default_system_message if present
        if "default_system_message" in config:
            # Prepend system message to prompt
            system_msg = config["default_system_message"]
            prompt = f"{system_msg}\n\n{prompt}"

        messages_for_llm = prompt

    # Add response_format for structured output if schema is present
    if schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response_schema",
                "schema": schema,
            },
        }

    if raw_response:
        kwargs["raw_response"] = True

    try:
        # Make the request
        if stream:
            # Streaming mode - client.complete() now handles display internally (ADR-0010)
            # and returns the complete response
            complete_response = client.complete(
                model=model, messages=messages_for_llm, stream=True, **kwargs
            )

            # Validate against schema if present
            if schema is not None:
                try:
                    parsed_response = json.loads(complete_response)
                    validate_against_schema(parsed_response, schema)
                except json.JSONDecodeError as e:
                    print(
                        f"\nWarning: Response is not valid JSON: {e}", file=sys.stderr
                    )
                    sys.exit(1)
                except ConfigurationError as e:
                    print(f"\nValidation error: {e}", file=sys.stderr)
                    sys.exit(1)

            # Save conversation if in conversation mode
            if conversation is not None:
                conversation.add_message("user", prompt)
                conversation.add_message("assistant", complete_response)
                # Update token count
                try:
                    tokens = client.count_tokens(model, conversation.get_messages())
                    conversation.total_tokens = tokens
                except Exception:
                    pass  # Token counting is optional
                conversation_manager.save(conversation)
        else:
            # Non-streaming mode
            response = client.complete(model=model, messages=messages_for_llm, **kwargs)

            if raw_response:
                print(json.dumps(response, indent=2))
            else:
                # Validate against schema if present
                if schema is not None:
                    try:
                        parsed_response = json.loads(response)
                        validate_against_schema(parsed_response, schema)
                    except json.JSONDecodeError as e:
                        print(
                            f"Error: Response is not valid JSON: {e}", file=sys.stderr
                        )
                        print(f"Response: {response}", file=sys.stderr)
                        sys.exit(1)
                    except ConfigurationError as e:
                        print(f"Validation error: {e}", file=sys.stderr)
                        print(f"Response: {response}", file=sys.stderr)
                        sys.exit(1)

                print(response)

                # Save conversation if in conversation mode
                if conversation is not None:
                    conversation.add_message("user", prompt)
                    conversation.add_message("assistant", response)
                    # Update token count
                    try:
                        tokens = client.count_tokens(model, conversation.get_messages())
                        conversation.total_tokens = tokens
                    except Exception:
                        pass  # Token counting is optional
                    conversation_manager.save(conversation)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        # Close log file if it was opened
        if log_file_handle:
            log_file_handle.close()
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        # Close log file if it was opened
        if log_file_handle:
            log_file_handle.close()
        sys.exit(1)
    finally:
        # Ensure log file is closed
        if log_file_handle:
            log_file_handle.close()


if __name__ == "__main__":
    main()
