# cllm-repeater: A Command-Line Tool for Repeating Commands on JSON Data

## Overview

`cllm-repeater` is a command-line tool designed to execute a specified command (`cllm`) on each item in a JSON array. The tool reads input data from standard input, processes each item using the `cllm` command with provided arguments, and outputs the results in JSON format. It handles errors gracefully and attempts to parse the command output as JSON.

## Features

- Execute the `cllm` command on each item in a JSON array.
- Capture and parse the command output as JSON.
- Handle errors and provide meaningful error messages.
- Output the results in JSON format.

## Usage

To use `cllm-repeater`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- The script accepts any arguments that should be passed to the `cllm` command.

### Example Command

```bash
echo '[{"key": "value1"}, {"key": "value2"}]' | cllm-repeater --arg1 value1 --arg2 value2
```

### Detailed Steps

1. **Read Input Data**:
   The script reads JSON input data from standard input.

2. **Process Each Item**:
   For each item in the JSON array, the script executes the `cllm` command with the provided arguments. The item is passed as input to the command.

3. **Capture and Parse Output**:
   The script captures the command output and attempts to parse it as JSON. If parsing fails, the raw output is returned.

4. **Handle Errors**:
   If the `cllm` command is not found, an error message is appended to the results.

5. **Output Results**:
   The results are output in JSON format.

## Example Output

```json
[
  {
    "key": "value1",
    "result": {
      "output_key": "output_value1"
    }
  },
  {
    "key": "value2",
    "result": {
      "output_key": "output_value2"
    }
  }
]
```
