# CLLM-Prompt Command Documentation

The `cllm-prompt` command is a command-line interface (CLI) tool designed to generate prompts using Jinja2 templates. This tool allows users to create customized prompts by specifying various context parameters and templates.

## Usage

To use the `cllm-prompt` command, you can run it with the appropriate arguments and options. Below is a detailed explanation of the available commands and options.

### Commands

- `templates`: Lists all available templates.

### Options

- `-t, --template`: Define a prompt template. Default is `default`.
- `-l, --list`: List available templates.
- `-pr, --prompt-role`: Specify the role prompt. Default is `PROMPT_ROLE`.
- `-pi, --prompt-instructions`: Specify the instructions prompt. Default is `PROMPT_INSTRUCTIONS`.
- `-pc, --prompt-context`: Specify the context prompt. Default is `PROMPT_CONTEXT`.
- `-po, --prompt-output`: Specify the output prompt. Default is `PROMPT_OUTPUT`.
- `-pe, --prompt-example`: Specify the example prompt. Default is `PROMPT_EXAMPLE`.
- `--cllm-dir`: Path to the CLLM directory. Default is `CLLM_DIR`.
- `prompt_input`: Input for the prompt. Default is `PROMPT_INPUT`.

### Example Usage

By default, `cllm-prompt` expects that a `.cllm` folder exists in the specified directory. This folder should contain the `templates` directory. You can override this by setting the `CLLM_DIR` environment variable.

#### Listing Available Templates

To list all available templates, use the `--list` option:

```bash
cllm-prompt --list
```

#### Generating a Prompt with Default Template

To generate a prompt using the default template, you can run:

```bash
cllm-prompt -pi "Who are the members of the Beatles?"
```

#### Generating a Prompt with a Custom Template

To generate a prompt using a custom template, specify the template name with the `-t` option:

```bash
cllm-prompt -t custom_template -pi "Who are the members of the Beatles?"
```

#### Providing Additional Context

You can provide additional context for the prompt using the `--prompt-context` option:

```bash
cllm-prompt -pc "I want to know more about British rock." -pi "Who are the members of the Beatles?"
```

### Environment Variables

You can also set environment variables to provide default values for the options.

- `CLLM_TEMPLATE`
- `CLLM_PROMPT_ROLE`
- `CLLM_PROMPT_INSTRUCTIONS`
- `CLLM_PROMPT_CONTEXT`
- `CLLM_PROMPT_OUTPUT`
- `CLLM_PROMPT_EXAMPLE`
- `CLLM_DIR`
- `CLLM_PROMPT_INPUT`

### Example with Environment Variables

```bash
export CLLM_TEMPLATE="default"
export CLLM_PROMPT_INSTRUCTIONS="These are the instructions"
cllm-prompt
```

### Variable Precedence

The order of precedence for variables is as follows:

1. Command line options
2. Environment variables
3. Default values

## Prompt Templating

The prompt variables are broken down into the following categories:

- `PROMPT_ROLE`: Tells the model who to be.
- `PROMPT_INSTRUCTIONS`: Instructions about what you want the model to do.
- `PROMPT_CONTEXT`: Background context or additional information for the prompt.
- `PROMPT_OUTPUT`: Tell the model what you want the output to be.
- `PROMPT_EXAMPLE`: Provides the model with an example of what you want the output to look like.

### Default Template

The `default` template is found in the `$CLLM_DIR/templates/default.tpl` file, which looks like this:

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
OUTPUT:
{{PROMPT_OUTPUT}}
{% endif %}
{% if PROMPT_EXAMPLE %}
EXAMPLE:
{{PROMPT_EXAMPLE}}
{% endif %}
```

### Custom Templates

You can add custom templates by creating a new `.tpl` file in the `$CLLM_DIR/templates` directory.

### Example with Custom Template

The `qa` template is found in the `$CLLM_DIR/templates/qa.tpl` file:

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
cllm-prompt -t qa -pc "I want to know more about British rock." -pi "Who are the members of the Beatles?"
```

Stdin can be used to provide additional context. Instructions can be passed to the model using quoted strings like this:

```bash
echo "I want to know more about British rock." | cllm-prompt -t qa -pi "Who are the members of the Beatles?"
```

## Conclusion

The `cllm-prompt` command provides a flexible and powerful way to generate prompts using templates. By leveraging the options and environment variables, you can customize the prompts to fit your specific needs.
