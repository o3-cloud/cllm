# cllm-load-files: A Command-Line Tool for Loading and Processing Files

## Overview

`cllm-file-load` is a command-line tool designed to load files, split the content into chunks, and convert the processed data into JSON format. The tool provides options to customize the chunk size and overlap, making it versatile for various text processing needs.

## Features

- Load files specified by the user.
- Split file content into chunks with customizable size and overlap.
- Convert the processed data into JSON format.
- Print the JSON data to the console.

## Usage

To use `cllm-file-load`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- `files`: **(Required)** A JSON string representing a list of files to load.
- `-s`, `--chunk_size`: The size of each chunk. Default is `1000`.
- `-o`, `--chunk_overlap`: The number of characters that overlap between chunks. Default is `10`.

### Example Command

```bash
cllm-load-files '["file1.txt", "file2.txt"]' -s 500 -o 50
```

### Detailed Steps

1. **Load Files**:
   The script uses the `UnstructuredFileLoader` to load the specified files.

2. **Split File Content**:
   The content of the loaded files is split into chunks using the `RecursiveCharacterTextSplitter`. The chunk size and overlap can be customized.

3. **Convert to JSON**:
   The processed data is converted into JSON format, where each chunk is represented as an object with `page_content` and `metadata`.

4. **Print JSON Data**:
   The JSON data is printed to the console.

## Example Output

```json
[
  {
    "page_content": "This is a chunk of text from the file.",
    "metadata": {
      "file_name": "file1.txt",
      "chunk_index": 0
    }
  },
  {
    "page_content": "This is another chunk of text from the file.",
    "metadata": {
      "file_name": "file1.txt",
      "chunk_index": 1
    }
  }
]
```