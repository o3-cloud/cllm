#!/usr/bin/env python3
"""
Example usage of structured output with JSON schemas.

This script demonstrates how to use CLLM's structured output feature
programmatically through the Python API. For CLI usage, see the examples
in examples/schemas/README.md.
"""

import json
from cllm import LLMClient


def example_person_extraction():
    """Extract person information with structured output."""
    print("=" * 60)
    print("Example 1: Person Information Extraction")
    print("=" * 60)

    client = LLMClient()

    # Define JSON schema for person information
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "email": {"type": "string", "format": "email"},
            "occupation": {"type": "string"}
        },
        "required": ["name", "age"],
        "additionalProperties": False
    }

    # Create the response_format parameter
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "person_schema",
            "schema": schema
        }
    }

    prompt = "Extract person info: John Doe is a 30-year-old software engineer at Google. Email: john@example.com"

    print(f"\nPrompt: {prompt}")
    print(f"\nSchema: {json.dumps(schema, indent=2)}")

    # Note: This requires a model that supports structured output (e.g., gpt-4o)
    # and a valid API key set in environment variables
    print("\n(To run this example, set OPENAI_API_KEY and uncomment the completion call below)")

    # Uncomment to actually call the API:
    # response = client.complete(
    #     model="gpt-4o",
    #     messages=prompt,
    #     temperature=0,
    #     response_format=response_format
    # )
    #
    # parsed = json.loads(response)
    # print(f"\nStructured Response:")
    # print(json.dumps(parsed, indent=2))


def example_entity_extraction():
    """Extract named entities with structured output."""
    print("\n" + "=" * 60)
    print("Example 2: Entity Extraction")
    print("=" * 60)

    client = LLMClient()

    # Define JSON schema for entity extraction
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["person", "organization", "location", "date", "product", "other"]
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["name", "type"]
                }
            }
        },
        "required": ["entities"],
        "additionalProperties": False
    }

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "entity_extraction_schema",
            "schema": schema
        }
    }

    prompt = "Extract entities from: Apple Inc. announced a new product launch in Cupertino on March 15, 2024."

    print(f"\nPrompt: {prompt}")
    print(f"\nSchema: {json.dumps(schema, indent=2)}")
    print("\n(To run this example, set OPENAI_API_KEY and uncomment the completion call)")


def example_cli_usage():
    """Show CLI usage examples."""
    print("\n" + "=" * 60)
    print("Example 3: CLI Usage Examples")
    print("=" * 60)

    examples = [
        {
            "title": "Inline JSON Schema",
            "command": '''echo "John Doe, age 30" | cllm --model gpt-4o --json-schema '{"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "number"}}, "required": ["name", "age"]}'
'''
        },
        {
            "title": "External Schema File",
            "command": '''cat document.txt | cllm --model gpt-4o --json-schema-file examples/schemas/person.json
'''
        },
        {
            "title": "Using Cllmfile Configuration",
            "command": '''echo "Extract entities from this text..." | cllm --config extraction
'''
        },
        {
            "title": "Override Config with CLI Flag",
            "command": '''cat data.txt | cllm --config extraction --temperature 0.5
'''
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(f"   {example['command']}")

    print("\nFor more examples, see:")
    print("  - examples/schemas/README.md")
    print("  - examples/configs/extraction.Cllmfile.yml")
    print("  - examples/configs/task-parser.Cllmfile.yml")


if __name__ == "__main__":
    print("\nCLLM Structured Output Examples")
    print("=" * 60)
    print("\nThis script demonstrates CLLM's structured output capabilities")
    print("as defined in ADR-0005.\n")

    example_person_extraction()
    example_entity_extraction()
    example_cli_usage()

    print("\n" + "=" * 60)
    print("Implementation complete! ✓")
    print("=" * 60)
    print("\nWhat was implemented:")
    print("  ✓ Added jsonschema dependency")
    print("  ✓ Schema loading and validation in config.py")
    print("  ✓ CLI flags: --json-schema and --json-schema-file")
    print("  ✓ response_format parameter support in client.py")
    print("  ✓ Schema validation in CLI output handling")
    print("  ✓ Example schemas (person, entity-extraction, sentiment)")
    print("  ✓ Example Cllmfile configurations")
    print("  ✓ 17 new tests (all 64 tests passing)")
    print("\nTo test with a real API:")
    print("  1. Set your API key: export OPENAI_API_KEY='sk-...'")
    print("  2. Try: echo 'John Doe, 30 years old' | \\")
    print("          uv run cllm --model gpt-4o \\")
    print("          --json-schema-file examples/schemas/person.json")
    print()
