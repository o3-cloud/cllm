# cllm-load-dir: A Command-Line Tool for Loading and Processing Directory Files

## Overview

`cllm-load-dir` is a command-line tool designed to load files from a specified directory, split the content into chunks, and convert the processed data into JSON format. The tool supports multithreading for efficient file loading and provides options to customize the chunk size and overlap.

## Features

- Load files from a specified directory using a glob pattern.
- Split file content into chunks with customizable size and overlap.
- Convert the processed data into JSON format.
- Save the JSON data to a specified output file.
- Support for multithreading to speed up file loading.

## Usage

To use `cllm-load-dir`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- `-d`, `--directory`: **(Required)** The directory to load files from.
- `-g`, `--glob_pattern`: The glob pattern to match files. Default is `**/*`.
- `-s`, `--chunk_size`: The size of each chunk. Default is `1000`.
- `-o`, `--chunk_overlap`: The number of characters that overlap between chunks. Default is `10`.
- `-m`, `--use_multithreading`: Use multithreading for loading files. Default is `True`.
- `-f`, `--output_file`: The output file for the JSON data.

### Example Command

```bash
cllm-load-dir -d /path/to/directory -g "*.txt" -s 500 -o 50 -m True -f output.json
```

### Detailed Steps

1. **Load Files from Directory**:
   The script uses the `DirectoryLoader` to load files from the specified directory based on the provided glob pattern.

2. **Split File Content**:
   The content of the loaded files is split into chunks using the `RecursiveCharacterTextSplitter`. The chunk size and overlap can be customized.

3. **Convert to JSON**:
   The processed data is converted into JSON format using the `convert_docs_to_json` function.

4. **Save JSON to File**:
   If an output file is specified, the JSON data is saved to the file using the `save_json_to_file` function.

5. **Print JSON Data**:
   The JSON data is printed to the console.

## Example Output

```json
[
  {
    "page_content": "This is a chunk of text from the file.",
    "metadata": {
      "file_name": "example.txt",
      "chunk_index": 0
    }
  },
  {
    "page_content": "This is another chunk of text from the file.",
    "metadata": {
      "file_name": "example.txt",
      "chunk_index": 1
    }
  }
]
```

## Logging

The script uses Python's `logging` module to log messages. The log level can be set using the `LOGLEVEL` environment variable.

## Conclusion

`cllm-load-dir` is a versatile tool for loading, processing, and converting directory files into JSON format. With customizable options and support for multithreading, it is designed to handle various use cases efficiently.
