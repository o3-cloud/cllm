# Command Line LLM (cllm) Toolkit

<p align="center">
  <img src="images/logo.png" width="250">
  <br>
  <em>Image generated using <a href="examples/logo/cllm-clam.sh">cllm-clam.sh</a></em>
</p>


Command Line LLM (cllm) Toolkit is a command line tool for interfacing with LLM models. It is designed to be a simple and easy to use tool for generating text from a prompts. It includes a suite of tools for interfacing with `cllm` output to build more complex prompt chaining processes.

## Why?

Most of us were introduced to LLMs through the ChatGPT GUI. The GUI is great for getting started, but it is limiting. You can't easily interface with files and other programs. It's not ideal for more complex workflows. Exactly what it is doing under the hood is magic.

Prompt Chaining Libraries are very powerful and make it possible to build complex workflows, but they can hide a lot of what is happening under the hood around prompt generation, chaining, and function calling.

Notebooks are great for documentation prototyping and sharing, but they are not ideal for building complex workflows and deploying your projects. 

Agent frameworks are great for getting complex agent workflows up and running quickly, but they hide a lot of what is happening under the hood. Their configuration can be complex and very opinionated.

The `cllm` toolkit attempts to solve these issues by being bash centric. Allowing you to chain LLM inference process with all the bash commands you are familiar using bash pipeing. Also giving you a suite of tools such as Vector Stores, Text Splitters, Data Loaders, and Ouput Parsers for building more complex prompt chaining flows all using bash scripting.

## Requirements

- Python 3.8+
- Poetry
- OpenAI API Key set as `OPENAI_API_KEY` environment variable

### Recommended

- jq
- Ollama

## Note

So far this has only been verified on MacOS. It should work on Linux. It may work on Windows, but I have not tested it.


## Installation

```
git clone git@github.com:o3-cloud/cllm.git

cd cllm

poetry install
poetry shell
```

### Installing `cllm` Command Globally

For ease of use you can install the `cllm` command globally.

bash
```
echo "export PATH=\$PATH:${VIRTUAL_ENV}/bin" >> ~/.bashrc
echo "export CLLM_DIR=\$HOME/.cllm" >> ~/.bashrc
```

zsh
```
echo "export PATH=\$PATH:${VIRTUAL_ENV}/bin" >> ~/.zprofile
echo "export CLLM_DIR=\$HOME/.cllm" >> ~/.zprofile
```

Copy the `.cllm` directory to your home directory.
    
```
cp -r .cllm ~/.cllm
```

### Via Docker

```
docker build -t cllm .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY --rm cllm gpt/3.5 "What is the meaning of life?"
```

Accepting stdin

```
cat README.md | docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -i --rm cllm -t qa gpt/4o "How do I use cllm with docker and stdin?"
```

## CLLM Command

Here is an example of how you might use the `cllm` toolkit to generate text from a prompt.

```
cllm gpt/3.5 "What is the meaning of life?"
```

To learn more about the `cllm` command see the [cllm](docs/cllm.md) documentation.

For more examples see the [examples](examples) directory.

# Toolkit

In addition to the `cllm` command, the `cllm` toolkit includes a suite of tools for interfacing with `cllm` output to build more complex prompt chaining processes.

To learn more about the toolkit see the [toolkit](docs/toolkit/) documentation.

See the [toolkit](docs/toolkit/) directory for more information on how to use the toolkit commands.