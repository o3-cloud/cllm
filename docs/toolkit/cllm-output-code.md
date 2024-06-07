# cllm-output-code CLI Tool

## Usage

The `cllm-output-code` CLI tool provides a way to process and optionally install dependencies for code provided via standard input. Below are the available command-line arguments for this tool:

### Arguments

- `-s`, `--skip-dependencies`
  - **Description**: Skip installing dependencies.
  - **Usage**: Use this flag if you do not want the tool to install any dependencies specified in the input data.
  - **Example**: 
    ```sh
    echo '{"code": "print(\"Hello, World!\")", "dependencies": ["requests"], "type": "python"}' | cllm-output-code -s
    ```

### Example Usage

To run the tool without skipping dependencies:
```sh
echo '{"code": "print(\"Hello, World!\")", "dependencies": ["requests"], "type": "python"}' | cllm-output-code
```

To run the tool and skip installing dependencies:
```sh
echo '{"code": "print(\"Hello, World!\")", "dependencies": ["requests"], "type": "python"}' | cllm-output-code -s
```

In both examples, the input data is provided via standard input using `echo` and a pipe (`|`). The input data should be a JSON string containing the code, dependencies, and type.
