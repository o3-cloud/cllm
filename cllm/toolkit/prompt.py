import argparse
import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from tabulate import tabulate
import yaml
import logging
from typing import Dict, Any
from cllm.constants import *

# Constants
TEMPLATES_DIR = "templates"
TEMPLATE_FILE_EXTENSION = ".tpl"
DEFAULT_TEMPLATE = "default"

# Configure logging
logging.basicConfig(level=os.environ.get("CLLM_LOGLEVEL"))
logger = logging.getLogger(__name__)

def list_available_items(directory: str, headers: list) -> None:
    """List available items in a directory and print them in a table format."""
    table_data = []
    for path in [str(f) for f in Path(directory).rglob('*') if f.is_file()]:
        name = path.replace(f"{directory}/", "").replace(TEMPLATE_FILE_EXTENSION, "")
        table_data.append(name)
    print(table_data)

def generate_prompt_from_template(template_name: str, cllm_dir: str, context: Dict[str, Any]) -> str:
    """Generate a prompt from a Jinja2 template."""
    template_env = Environment(loader=FileSystemLoader(f"{cllm_dir}/{TEMPLATES_DIR}"))
    template = template_env.get_template(f"{template_name}.tpl")
    return template.render(**context)

def build_cllm_prompt(template: str, cllm_dir: str, context: Dict[str, Any]) -> str:
    """Build the CLLM prompt based on the provided template and context."""
    return generate_prompt_from_template(template, cllm_dir, context)

def handle_templates_command(cllm_dir: str) -> None:
    """Handle the 'templates' command by listing available templates."""
    print("Available templates:")
    list_available_items(f"{cllm_dir}/{TEMPLATES_DIR}", ["name"])
    sys.exit(0)

def main() -> None:
    """Main entry point for the Template CLI."""
    parser = argparse.ArgumentParser(description="Template CLI for generating prompts")
    parser.add_argument("-t", "--template", help="Template name", default='default')
    parser.add_argument("-l", "--list", help="List available templates", action="store_true")
    parser.add_argument("-pr", "--prompt-role", help="Specify the role prompt", default=PROMPT_ROLE)
    parser.add_argument("-pi", "--prompt-instructions", help="Specify the instructions prompt", default=PROMPT_INSTRUCTIONS)
    parser.add_argument("-pc", "--prompt-context", help="Specify the context prompt", default=PROMPT_CONTEXT)
    parser.add_argument("-po", "--prompt-output", help="Specify the output prompt", default=PROMPT_OUTPUT)
    parser.add_argument("-pe", "--prompt-example", help="Specify the example prompt", default=PROMPT_EXAMPLE)
    parser.add_argument("--cllm-dir", help="Path to the cllm directory", default=CLLM_DIR)
    parser.add_argument("prompt_input", nargs='?', help="Input for the prompt", default=PROMPT_INPUT)
    
    args = parser.parse_args()

    context = {
        "PROMPT_ROLE": args.prompt_role,
        "PROMPT_INSTRUCTIONS": args.prompt_instructions,
        "PROMPT_CONTEXT": args.prompt_context,
        "PROMPT_OUTPUT": args.prompt_output,
        "PROMPT_EXAMPLE": args.prompt_example,
        "PROMPT_INPUT": args.prompt_input,
        "PROMPT_STDIN": None
    }

    if not sys.stdin.isatty():
        context['PROMPT_STDIN'] = sys.stdin.read().strip()

    if args.list:
        handle_templates_command(args.cllm_dir)
        exit(0)
   
    prompt = build_cllm_prompt(args.template, args.cllm_dir, context)
    print(prompt)

if __name__ == '__main__':
    main()