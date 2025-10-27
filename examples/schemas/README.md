# JSON Schema Examples for CLLM

This directory contains example JSON schemas for structured output from LLMs. These schemas can be used with CLLM's `--json-schema-file` flag or referenced in Cllmfile configurations.

## Available Schemas

### person.json
Extracts information about a person from text.

**Usage:**
```bash
echo "John Doe is a 30-year-old software engineer at Google. Contact: john@example.com" | \
  cllm --model gpt-4o --json-schema-file examples/schemas/person.json
```

**Output:**
```json
{
  "name": "John Doe",
  "age": 30,
  "email": "john@example.com",
  "occupation": "software engineer"
}
```

### entity-extraction.json
Extracts named entities from text with type classification.

**Usage:**
```bash
echo "Apple Inc. announced a new product launch in Cupertino on March 15, 2024." | \
  cllm --model gpt-4o --json-schema-file examples/schemas/entity-extraction.json
```

**Output:**
```json
{
  "entities": [
    {"name": "Apple Inc.", "type": "organization", "confidence": 0.95},
    {"name": "Cupertino", "type": "location", "confidence": 0.90},
    {"name": "March 15, 2024", "type": "date", "confidence": 0.98}
  ]
}
```

### sentiment.json
Analyzes sentiment and emotions in text.

**Usage:**
```bash
echo "I absolutely love this product! It exceeded all my expectations." | \
  cllm --model gpt-4o --json-schema-file examples/schemas/sentiment.json
```

**Output:**
```json
{
  "sentiment": "positive",
  "score": 0.9,
  "emotions": ["joy", "surprise"],
  "explanation": "The text expresses strong positive sentiment with enthusiastic language."
}
```

## Using Schemas in Cllmfile

You can reference these schemas in your Cllmfile configurations:

**extraction.Cllmfile.yml:**
```yaml
model: "gpt-4o"
temperature: 0
json_schema_file: "examples/schemas/entity-extraction.json"
```

Then use it:
```bash
cat document.txt | cllm --config extraction
```

## Creating Custom Schemas

JSON schemas should follow the JSON Schema specification (Draft 7). Key elements:

- `type`: The data type (object, array, string, number, boolean, null)
- `properties`: Object properties and their schemas
- `required`: Array of required property names
- `items`: Schema for array items
- `enum`: Allowed values for a field
- `minimum`/`maximum`: Numeric constraints
- `additionalProperties`: Whether extra properties are allowed

**Example:**
```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "count": {"type": "number", "minimum": 0}
  },
  "required": ["title"],
  "additionalProperties": false
}
```

## Path Resolution

When using `--json-schema-file` or `json_schema_file` in Cllmfile:

1. **Relative paths** are checked in:
   - Current working directory (where you run `cllm`)
   - `.cllm/` folder

2. **Absolute paths** are used as-is

**Examples:**
```bash
# Relative path (checks ./examples/schemas/person.json, then ./.cllm/examples/schemas/person.json)
cllm --json-schema-file examples/schemas/person.json "Extract person info"

# Absolute path
cllm --json-schema-file /Users/me/schemas/custom.json "Extract data"
```

## Validating Schemas

Before using a schema with an LLM, you can validate it using the `--validate-schema` flag:

```bash
# Validate an inline schema
cllm --validate-schema --json-schema '{"type": "object", "properties": {"name": {"type": "string"}}}'

# Validate an external schema file
cllm --validate-schema --json-schema-file examples/schemas/person.json

# Validate schema from Cllmfile
cllm --validate-schema --config extraction
```

This command will:
- Check if the schema is valid JSON Schema (Draft 7)
- Display schema details (type, properties, required fields)
- Exit with code 0 if valid, code 1 if invalid
- Not make any LLM API calls (free to test)

**Example output:**
```
✓ Schema is valid!

Schema details:
  Type: object
  Properties: 4
  Fields:
    - name: string (required)
    - age: number (required)
    - email: string (optional)
    - occupation: string (optional)

✓ Schema validation successful
```

## Tips

- Use `--validate-schema` to test your schemas before making API calls
- Use `temperature: 0` for more deterministic structured output
- Test your schemas with simple examples first
- Use descriptive field names and add `description` fields for better LLM understanding
- Set `additionalProperties: false` to prevent extra fields
- Use `enum` to constrain string values to specific choices
- Add format validation (e.g., `"format": "email"`) for additional validation

## Provider Compatibility

Structured output support varies by provider:

- **OpenAI**: Full support (GPT-4o, GPT-4o-mini recommended)
- **Anthropic**: Supported via function calling approach
- **Google Gemini**: Limited support
- **Other providers**: Check LiteLLM documentation

If a provider doesn't support structured output, you may get an error. CLLM will validate the output against your schema regardless of provider support.
