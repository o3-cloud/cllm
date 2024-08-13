import argparse
import base64
import json
from pathlib import Path
import sys
import jsonschema
from litellm import completion
from tabulate import tabulate
from jinja2 import Environment, FileSystemLoader
import os
import yaml
from typing import Optional, Dict, Any
import logging
from .constants import *

# Constants
SYSTEMS_DIR = "systems"
SCHEMAS_DIR = "schemas"
TEMPLATES_DIR = "templates"
CONTEXTS_DIR = "contexts"
DEFAULT_TEMPLATE = "default"
CONFIG_FILE_EXTENSION = ".yml"
JSON_FILE_EXTENSION = ".json"

# Configure logging
logging.basicConfig(level=os.environ.get("CLLM_LOGLEVEL"))
logger = logging.getLogger(__name__)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")
        sys.exit(1)


def list_available_items(directory: str, headers: list) -> None:
    """List available items in a directory and print them in a table format."""
    table_data = []
    for path in [str(f) for f in Path(directory).rglob('*') if f.is_file()]:
        data = load_yaml_file(path)
        name = path.replace(f"{directory}/", "").replace(CONFIG_FILE_EXTENSION, "")
        table_data.append([name] + [data.get(header) for header in headers[1:]])
    print(tabulate(table_data, headers, tablefmt="grid"))


def generate_prompt_from_template(template_name: str, cllm_dir: str, context: Dict[str, Any]) -> str:
    """Generate a prompt from a Jinja2 template."""
    template_env = Environment(loader=FileSystemLoader(f"{cllm_dir}/{TEMPLATES_DIR}"))
    template = template_env.get_template(f"{template_name}.tpl")
    return template.render(**context)


def validate_response_with_schema(response_content: str, json_schema: str) -> None:
    """Validate a JSON response against a schema."""
    try:
        jsonschema.validate(instance=json.loads(response_content), schema=json.loads(json_schema))
    except jsonschema.ValidationError as e:
        raise ValueError(f"Schema validation error: {e.message}")


def get_system_config(command: str, cllm_dir: str) -> Optional[Dict[str, Any]]:
    """Get the system configuration for a given command."""
    system_config_path = f"{cllm_dir}/{SYSTEMS_DIR}/{command}{CONFIG_FILE_EXTENSION}"
    if os.path.exists(system_config_path):
        return load_yaml_file(system_config_path)
    return None


def build_cllm_prompt(template: str, cllm_dir: str, context: Dict[str, Any]) -> str:
    """Build the CLLM prompt based on the provided template and context."""
    return generate_prompt_from_template(template, cllm_dir, context)


def handle_systems_command(cllm_dir: str) -> None:
    """Handle the 'systems' command by listing available systems."""
    print("Available systems:")
    list_available_items(f"{cllm_dir}/{SYSTEMS_DIR}", ["name", "description", "provider", "model"])
    sys.exit(0)


def handle_schemas_command(cllm_dir: str) -> None:
    """Handle the 'schemas' command by listing available schemas."""
    print("Available schemas:")
    list_available_items(f"{cllm_dir}/{SCHEMAS_DIR}", ["name", "description"])
    sys.exit(0)


def is_file(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path)


def cllm(command: str,
         template: Optional[str], 
         schema: Optional[str], 
         chat_context: Optional[str],
         chat_context_path: Optional[str],
         prompt_primer: Optional[str], 
         prompt_system: Optional[str], 
         prompt_role: Optional[str],
         prompt_instructions: Optional[str],
         prompt_context: Optional[str],
         prompt_output: Optional[str],
         prompt_example: Optional[str],
         temperature: Optional[float],
         cllm_dir: str,
         prompt_input: Optional[str],
         prompt_stdin: Optional[str],
         image_prompt: Optional[str],
         cllm_trace_id: Optional[str],
         dry_run: bool,
         max_messages: Optional[int] = None,
         streaming: bool = False) -> str:
    """Main function to handle CLLM commands and generate prompts."""

    if command == 'systems':
        handle_systems_command(cllm_dir)

    if command == 'schemas':
        handle_schemas_command(cllm_dir)

    cllm_prompt = ""
    if template:
        context = {
            "PROMPT_ROLE": prompt_role,
            "PROMPT_INSTRUCTIONS": prompt_instructions,
            "PROMPT_CONTEXT": prompt_context,
            "PROMPT_INPUT": prompt_input,
            "PROMPT_STDIN": prompt_stdin,
            "PROMPT_OUTPUT": prompt_output,
            "PROMPT_EXAMPLE": prompt_example
        }
        cllm_prompt = build_cllm_prompt(template, cllm_dir, context)

    system_config = get_system_config(command, cllm_dir)
    if not system_config:
        logger.error(f"No system configuration found for system '{command}'")
        sys.exit(1)

    if schema:
        schema_path = f"{cllm_dir}/{SCHEMAS_DIR}/{schema}{CONFIG_FILE_EXTENSION}"
        schema_config = load_yaml_file(schema_path)
        context = {
            "SCHEMA_JSON": schema_config.get('schema'),
            "SCHEMA_INSTRUCTIONS": prompt_input,
            "SCHEMA_OUTPUT": schema_config.get('prompt'),
            "SCHEMA_EXAMPLE": schema_config.get('example'),
            "PROMPT_INSTRUCTIONS": prompt_instructions,
            "PROMPT_CONTEXT": prompt_context,
            "PROMPT_INPUT": prompt_input,
            "PROMPT_STDIN": prompt_stdin,
        }
        cllm_prompt = build_cllm_prompt("schema", cllm_dir, context)

    provider = system_config.get('provider')
    model = system_config.get('model')
    model = f"{provider}/{model}"
    system_temperature = temperature if temperature is not None else system_config.get('temperature')
    system_prompt = prompt_system if prompt_system is not None else system_config.get('system_prompt')

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if chat_context_path:
        chat_context_path = f"{chat_context_path}/{chat_context}{JSON_FILE_EXTENSION}"
    else:
        chat_context_path = f"{cllm_dir}/{CONTEXTS_DIR}/{chat_context}{JSON_FILE_EXTENSION}"

    if chat_context:
        try:
            with open(chat_context_path, 'r') as f:
                messages = json.loads(f.read())
        except FileNotFoundError:
            pass

    if prompt_primer:
        messages.append({"role": "user", "content": prompt_primer})

    if image_prompt:
        if is_file(image_prompt):
            with open(image_prompt, "rb") as image_file:
                image_prompt = f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
        
        messages.append({"role": "user", "content": [
            {
                "type": "text",
                "text": cllm_prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": image_prompt
                }
            }
        ]
        })
    else:
        messages.append({"role": "user", "content": cllm_prompt})

    if max_messages is not None and len(messages) > max_messages:
        messages = messages[-max_messages:]

    if dry_run:
        return cllm_prompt

    try:
        response = completion(model=model,
                              temperature=system_temperature,
                              messages=messages,
                              stream=streaming)

        response_message = []
        if streaming:

            for part in response:
                message = part.choices[0].delta.content or ""
                if message:
                    response_message.append(message)
                    print(message, end="")

            response_message = "".join(response_message)
                
        else:
            response_message = response.choices[0].message.content

            if schema:
                validate_response_with_schema(response_message, schema_config.get('schema'))
            
        if chat_context:
            messages.append({"role": "assistant", "content": response_message})
            if max_messages is not None and len(messages) > max_messages:
                messages = messages[-max_messages:]
            with open(chat_context_path, 'w') as f:
                f.write(json.dumps(messages, indent=4))
                
        return response_message

    except Exception as e:
        logger.error(f"Failed to call OpenAI API: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLLM command-line interface."""
    parser = argparse.ArgumentParser(description="Command Line Language Model (CLLM) Interface")
    parser.add_argument("command", nargs='?',
                        help="Command to execute", 
                        default=COMMAND)
    parser.add_argument("-t", "--template", help="Define a prompt template", default=TEMPLATE)
    parser.add_argument("-s", "--schema", help="Specify the schema file", default=SCHEMA)
    parser.add_argument("-c", "--chat-context", help="Specify the chat context", default=CHAT_CONTEXT)
    parser.add_argument("-cp", "--chat-context-path", help="Specify the chat context path", default=None)
    parser.add_argument("-pp", "--prompt-primer", help="Primer prompt input", default=PROMPT_PRIMER)
    parser.add_argument("-ps", "--prompt-system", help="Specify the system prompt", default=PROMPT_SYSTEM)
    parser.add_argument("-pr", "--prompt-role", help="Specify the role prompt", default=PROMPT_ROLE)
    parser.add_argument("-pi", "--prompt-instructions", help="Specify the instructions prompt", default=PROMPT_INSTRUCTIONS)
    parser.add_argument("-pc", "--prompt-context", help="Specify the context prompt", default=PROMPT_CONTEXT)
    parser.add_argument("-po", "--prompt-output", help="Specify the output prompt", default=PROMPT_OUTPUT)
    parser.add_argument("-i", "--image", help="Specify an image path or URL for the prompt", default=IMAGE_PROMPT)
    parser.add_argument("-pe", "--prompt-example", help="Specify the example prompt", default=PROMPT_EXAMPLE)
    parser.add_argument("-tp", "--temperature", type=float, help="Specify the temperature", default=TEMPERATURE)
    parser.add_argument("--dry-run", action="store_true", help="Output the prompt without executing")
    parser.add_argument("--cllm-dir", help="Path to the cllm directory", default=CLLM_DIR)
    parser.add_argument("--cllm-trace-id", help="Specify a trace id", default=CLLM_TRACE_ID)
    parser.add_argument("-mm", "--max-messages", type=int, help="Limit the number of saved messages in the chat context", default=None)
    parser.add_argument("prompt_input", nargs='?', help="Input for the prompt", default=PROMPT_INPUT)
    parser.add_argument("--streaming", action="store_true", help="Enable streaming mode", default=STREAMING)
    args = parser.parse_args()

    config = {
        "command": args.command,
        "template": args.template,
        "schema": args.schema,
        "chat_context": args.chat_context,
        "chat_context_path": args.chat_context_path,
        "prompt_primer": args.prompt_primer,
        "prompt_system": args.prompt_system,
        "prompt_role": args.prompt_role,
        "prompt_instructions": args.prompt_instructions,
        "prompt_context": args.prompt_context,
        "prompt_output": args.prompt_output,
        "prompt_example": args.prompt_example,
        "image_prompt": args.image,
        "temperature": args.temperature,
        "cllm_dir": args.cllm_dir,
        "prompt_input": args.prompt_input,
        "prompt_stdin": None,
        "cllm_trace_id": args.cllm_trace_id,
        "dry_run": args.dry_run,
        "max_messages": args.max_messages,
        "streaming": args.streaming
    }

    if not sys.stdin.isatty():
        config['prompt_stdin'] = sys.stdin.read().strip()

    response = cllm(**config)
    if not config.get("streaming"):
        print(response)


if __name__ == '__main__':
    main()
