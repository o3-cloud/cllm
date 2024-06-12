# cllm-splitter-docs: A Command-Line Tool for Splitting Text into Chunks

## Overview

`cllm-splitter-docs` is a command-line tool designed to split text documents into smaller chunks using the `RecursiveCharacterTextSplitter`. The tool allows customization of chunk size and overlap, making it suitable for various text processing tasks.

## Features

- Split text documents into chunks with customizable size and overlap.
- Convert the processed data into JSON format.
- Read input documents from standard input (stdin).
- Output the chunked text as JSON to standard output (stdout).

## Usage

To use `cllm-splitter-docs`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- `-s`, `--chunk_size`: The size of each chunk. Default is `1000`.
- `-o`, `--chunk_overlap`: The number of characters that overlap between chunks. Default is `10`.

### Example Command

```bash
cat input.json | cllm-splitter-docs -s 500 -o 50
```

### Detailed Steps

1. **Read Input Documents**:
   The script reads JSON-formatted documents from standard input (stdin). Each document should be a dictionary with at least a `"page_content"` key containing the text to be split.

2. **Split Text into Chunks**:
   The content of each document is split into chunks using the `RecursiveCharacterTextSplitter`. The chunk size and overlap can be customized using the command-line arguments.

3. **Convert to JSON**:
   The processed chunks are converted into JSON format.

4. **Output JSON Data**:
   The JSON data is printed to standard output (stdout).

## Example Input

The input should be a JSON array of documents, each with a `"page_content"` key. For example:

```json
[
  {
    "page_content": "This is a long text that needs to be split into smaller chunks.",
    "metadata": {
      "title": "Example Document"
    }
  }
]
```

## Example Output

The output will be a JSON array of chunked documents. For example:

```json
[
  {
    "page_content": "This is a long text that needs to be split into smaller",
    "metadata": {
      "title": "Example Document"
    }
  },
  {
    "page_content": "chunks.",
    "metadata": {
      "title": "Example Document"
    }
  }
]
```