# Command Line Language Model (CLLM) Interface

The Command Line Language Model (CLLM) Interface is a tool designed to facilitate interactions with language models via the command line. It provides various functionalities such as listing available systems and schemas, generating prompts from templates, and validating responses against schemas.

## Usage

To use the CLLM interface, you can run the `cllm` command followed by the appropriate arguments and options. Below is a detailed explanation of the available commands and options.

### Commands

- `list`: Lists all available systems.
- `schemas`: Lists all available schemas.

### Options

- `-t, --template`: Define a prompt template. Default is `default`.
- `-s, --schema`: Specify the schema file.
- `-c, --chat-context`: Specify the chat context.
- `-pp, --prompt-primer`: Primer prompt input.
- `-ps, --prompt-system`: Specify the system prompt.
- `-pr, --prompt-role`: Specify the role prompt.
- `-pi, --prompt-instructions`: Specify the instructions prompt.
- `-pc, --prompt-context`: Specify the context prompt.
- `-po, --prompt-output`: Specify the output prompt.
- `-pe, --prompt-example`: Specify the example prompt.
- `-tp, --temperature`: Specify the temperature.
- `--dry-run`: Output the prompt without executing.
- `--cllm-path`: Path to the CLLM directory. Default is the current working directory with `.cllm` appended.
- `--cllm-trace-id`: Specify a trace ID.
- `prompt_input`: Input for the prompt.

### Example Usage

By default `cllm` expects that a `.cllm` folder exists in the current working directory. This folder should contain the `systems`, `templates` and `schemas` directories. You can override this by setting the `CLLM_PATH` environment variable.

#### Listing Available Systems

```bash
cllm list
```

#### Listing Available Schemas

```bash
cllm schemas
```

#### Basic a Prompt Generation

```bash
cllm gpt/3.5 -pi "Who are the members of the Beatles?"
```

## Persistent Context

The `--chat-context` option can be used to provide a persistent context for the conversation. This context will be carried over between prompts.

```bash
CONTEXT_NAME="my_context"
cllm gpt/3.5 -c ${CONTEXT_NAME} -pi "Remember this squence of words. Apple, Banana, Cherry."
cllm gpt/3.5 -c ${CONTEXT_NAME} -pi "What comes after Banana?"
```

## Prompt Templating

The prompt variables are broken down into the following categories:

- prompt_instructions - Instructions about what you want the model to do
- prompt_context - Background context or additional information for the prompt
- prompt_role - Tells the model who to be
- prompt_output - Tell the model what you want the output to be
- prompt_example - Proves the model with an example of what you want the output to look like

You can inspect the rendered prompt by using the `--dry-run` flag.

```bash
cllm gpt/3.5 -pi "Who are the members of the Beatles?" --dry-run
```

In the above the the default template is used.

The `default` found in the $CLLM_PATH/templates/default.tpl file which looks like this:

```
{% if (PROMPT_CONTEXT or PROMPT_STDIN) %}
CONTEXT:
{{PROMPT_CONTEXT or ""}} 
{{PROMPT_STDIN or ""}}
{% endif %}
{% if PROMPT_ROLE %}
ROLE:
{{PROMPT_ROLE}}
{% endif %}
INSTRUCTIONS:
{{PROMPT_INSTRUCTIONS or ""}}
{{PROMPT_INPUT or ""}}
{% if PROMPT_OUTPUT %}
OUPUT:
{{PROMPT_OUTPUT}}
{% endif %}
{% if PROMPT_OUTPUT %}
EXAMPLE:
{{PROMPT_EXAMPLE}}
{% endif %}
```

### Generating a Prompt with a Template

The `qa` found in the $CLLM_PATH/templates/qa.tpl file:
```
{% if PROMPT_ROLE %}
ROLE:
{{PROMPT_ROLE}}
{% endif %}

QUESTION:
{{PROMPT_CONTEXT or ""}} 
{{PROMPT_STDIN or ""}}
{{PROMPT_INSTRUCTIONS or ""}}
{{PROMPT_INPUT or ""}}

ANSWER:
```

Using the `qa` template:

```bash
cllm -t qa -pi gpt/3.5 "Who are the members of the Beatles?" -pc "I want to know more about british rock."
```

You can add custom templates by creating a new `.tpl` file in the $CLLM_PATH/templates directory.

Stdin can be used to provide additional context.
Instruction can be passed to the model using quoted strings like this.

```bash
echo "You want to know more about british rock." | cllm -t qa gpt/3.5 "Who are the members of the Beatles?"
```

### Generating Consistant JSON with a Schema

```bash
cllm --schema list gpt/3.5 "Who are the members of the Beatles?"
```
When using a schema the template is ignored and the schema template is used.

The `schema` found in the $CLLM_PATH/templates/schema.tpl file:

```
CONTEXT:
{{PROMPT_CONTEXT or ""}}
{{PROMPT_STDIN or ""}}

SCHEMA:
{{SCHEMA_JSON}}

INSTRUCTIONS:
{{SCHEMA_INSTRUCTIONS or ""}}
{{PROMPT_INSTRUCTIONS or ""}}

OUPUT:
{{SCHEMA_OUTPUT}}

EXAMPLE:
{{SCHEMA_EXAMPLE}}
```

## Environment Variables

You can also set environment variables to provide default values for the options.
Environment variables take precedence over command line options.

- `CLLM_COMMAND`
- `CLLM_TEMPLATE`
- `CLLM_SCHEMA`
- `CLLM_CHAT_CONTEXT`
- `CLLM_PROMPT_PRIMER`
- `CLLM_PROMPT_SYSTEM`
- `CLLM_PROMPT_ROLE`
- `CLLM_PROMPT_INSTRUCTIONS`
- `CLLM_PROMPT_CONTEXT`
- `CLLM_PROMPT_OUTPUT`
- `CLLM_PROMPT_EXAMPLE`
- `CLLM_TEMPERATURE`
- `CLLM_PATH`
- `CLLM_TRACE_ID`
- `CLLM_PROMPT_INPUT`

### Example with Environment Variables

```bash
export CLLM_TEMPLATE="default"
export CLLM_PROMPT_INSTRUCTIONS="These are the instructions"
cllm gpt/3.5
```

