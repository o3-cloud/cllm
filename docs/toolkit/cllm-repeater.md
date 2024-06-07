# cllm-repeater CLI Tool

`cllm-repeater` is a command-line tool designed to process a list of data items by repeatedly invoking the `cllm` command with specified arguments. The tool reads input data from standard input, processes each item, and outputs the results in JSON format.

## Usage

```sh
cllm-repeater [args...]
```

### Arguments

- `[args...]`: A list of arguments to be passed to the `cllm` command. These arguments are appended to the `cllm` command for each item in the input data.

### Input

The input data should be provided via standard input (stdin) in JSON format. The JSON should be an array of items, where each item is a string that will be passed to the `cllm` command.

### Output

The output is a JSON array where each element corresponds to the result of processing an item from the input data. The results can be either parsed JSON objects (if the `cllm` command outputs valid JSON) or raw strings (if the output is not valid JSON). In case of a `FileNotFoundError`, the error message will be included in the output.

### Example

```sh
echo '["Party ideas", "Places to see"]' | cllm-repeater -s list gpt/3.5
```

In this example, the input data `["data1", "data2"]` is processed by the `cllm` command with the arguments `--option1 value1 --option2 value2`. The results are then printed in JSON format.

### Notes

- Ensure that the `cllm` command is available in your system's PATH.
- The tool captures both standard output and standard error from the `cllm` command.
- If the `cllm` command is not found, an error message will be included in the output.
