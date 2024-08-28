# CMD | LLM (cllm) Command Line Toolkit for LLMs

<p align="center">
  <img src="images/logo.png" width="250">
  <br>
  <em>Image generated using <a href="examples/logo/cllm-clam.sh">cllm-clam.sh</a></em>
</p>


CMD | LLM (cllm) Toolkit is a command line tool for interfacing with LLM models. It is designed to be a simple and easy to use tool for generating text from a prompts. It includes a suite of tools for interfacing with `cllm` output to build more complex prompt chaining processes.

## Why?

Most of us were introduced to LLMs through the ChatGPT GUI. The GUI is great for getting started, but it is limiting. You can't easily interface with files and other programs. It's not ideal for more complex workflows. Exactly what it is doing under the hood is magic.

Prompt Chaining Libraries are very powerful and make it possible to build complex workflows, but they can hide a lot of what is happening under the hood around prompt generation, chaining, and function calling.

Notebooks are great for documentation prototyping and sharing, but they are not ideal for building complex workflows and deploying your projects. 

Agent frameworks are great for getting complex agent workflows up and running quickly, but they hide a lot of what is happening under the hood. Their configuration can be complex and very opinionated.

The `cllm` toolkit attempts to solve these issues by being bash centric, allowing you to chain LLM inference processes with all the bash commands you are familiar with using bash piping. It also gives you a suite of tools such as Vector Stores, Text Splitters, Data Loaders, and Output Parsers for building more complex prompt chaining flows all using bash scripting.

## Requirements

- Python 3.8+
- Poetry
- OpenAI API Key set as `OPENAI_API_KEY` environment variable

### Recommended

- jq
- Additional LLM API Keys

## Note

So far this has only been verified on MacOS. It should work on Linux. It may work on Windows, but I have not tested it.


## Getting Started

```bash
git clone git@github.com:o3-cloud/cllm.git

cd cllm

poetry install
poetry shell

cllm
```

## Installing `cllm` Globally

To install the command to your default python environment, run a poetry build, then install the project's wheel.

```
rm -rf dist

poetry build
pip install dist/*.whl

cllm --help
```

Copy the `.cllm` directory to your home directory.

```
cp -r .cllm ~/.cllm
```

Then initialize the `CLLM_DIR` environment variable in your
`.bashrc` or `.zshrc`.

bash
```bash
echo "export CLLM_DIR=\$HOME/.cllm" >> ~/.bashrc
```

zsh
```bash
echo "export CLLM_DIR=\$HOME/.cllm" >> ~/.zshrc
```

## Running Via Docker

```
docker build -t cllm .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY --rm cllm gpt/3.5 "What is the meaning of life?"
```

Accepting stdin

```
cat README.md | docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -i --rm cllm -t qa gpt/4o "How do I use cllm with docker and stdin?"
```

## CLLM Directory

The `cllm` toolkit uses a `.cllm` directory in your home directory to store configuration files and data.
By default it checks the current working directory for a `.cllm` directory. If it does not find one, it will then use the one provided by the `CLLM_DIR` environment variable.

## CLLM Command

Here is an example of how you might use the `cllm` toolkit to generate text from a prompt.

```
cllm gpt/3.5 "What is the meaning of life?"
```

To learn more about the `cllm` command see the [cllm](docs/cllm.md) documentation.

For more examples see the [examples](examples) directory.

## Toolkit

In addition to the `cllm` command, the `cllm` toolkit includes a suite of tools for interfacing with `cllm` output to build more complex prompt chaining processes.

To learn more about the toolkit see the [toolkit](docs/toolkit/README.md) documentation.


## LLM Model Provides

The `cllm` command currently supports a large number of model providers:

| name | description | provider | model |
|------|-------------|----------|-------|
| base2 | A basic system. No system prompt is provided. | openai | gpt-4o |
| base | GPT-4o model provided by OpenAI | openai | gpt-4o |
| gemini/pro | Gemini Pro 1.5 model provided by Google gemini | gemini | gemini-1.5-pro |
| gemini/flash | Gemini Flash 1.5 model provided by Google Gemini | gemini | gemini-1.5-flash |
| gpt/4 | OpenAI gpt-4-turbo for general purpose. | openai | gpt-4-turbo |
| gpt/3.5 | OpenAI gpt-3.5-turbo for general purpose. | openai | gpt-3.5-turbo |
| gpt/4o | OpenAI gpt-4o for general purpose. | openai | gpt-4o |
| claude/opus | Claude 3.5 Opus model provided by Anthropic | anthropic | claude-3-opus-20240229 |
| claude/sonnet | Claude 3.5 Sonnet model provided by Anthropic | anthropic | claude-3-5-sonnet-20240620 |
| claude/haiku | Claude Haiku model provided by Anthropic | anthropic | claude-3-haiku-20240307 |
| groq/llama | Llama3 70b model provided by Groq | groq | llama3-70b-8192 |
| groq/gemma | Gemma 7b model provided by Groq | groq | gemma-7b-it |
| groq/mixtral | Mixtral 8x7b model provided by Groq | groq | mixtral-8x7b-32768 |
| bedrock/command-r | Cohere Command-R+ model provided by AWS bedrock | bedrock | cohere.command-r-plus-v1:0 |
| bedrock/llama | Llama3 70b model provided by AWS bedrock | bedrock | meta.llama3-70b-instruct-v1:0 |
| bedrock/sonnet | Antropic Claude Sonnet 3.5 model provided by AWS bedrock | bedrock | anthropic.claude-3-5-sonnet-20240620-v1:0 |
| bedrock/mistral | Mistral Mixtral 8x7b model provided by AWS bedrock | bedrock | mistral.mixtral-8x7b-instruct-v0:1 |
| bedrock/haiku | Anthropic Claude Haiku 3 model provided by AWS bedrock | bedrock | anthropic.claude-3-haiku-20240307-v1:0 |
| l/qwen | Qwen 0.5b model locally provided by Ollama | ollama | qwen:0.5b |
| l/llama | Llama3 7b model locally provided by Ollama | ollama | llama3 |
| l/phi | Phi3 7b model locally provided by Ollama | ollama | phi3 |            |


Additional models can be added by adding a new system.yml file to the `~/.cllm/systems` directory.
