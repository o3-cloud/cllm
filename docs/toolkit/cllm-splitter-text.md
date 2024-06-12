# cllm-splitter-text: A Command-Line Tool for Splitting Text into Chunks

## Overview

`cllm-splitter-text` is a command-line tool designed to split a given text into smaller chunks with customizable size and overlap. The tool reads text from standard input, processes it using the `RecursiveCharacterTextSplitter`, and outputs the chunks in JSON format.

## Features

- Split text into chunks with customizable size and overlap.
- Add metadata to each chunk.
- Output the processed chunks in JSON format.

## Usage

To use `cllm-splitter-text`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- `-s`, `--chunk_size`: The size of each chunk. Default is `100`.
- `-o`, `--chunk_overlap`: The number of characters that overlap between chunks. Default is `20`.
- `-m`, `--metadata`: Associated metadata in JSON format. Default is `{}`.

### Example Command

```bash
echo "Your text here" | cllm-splitter-doc -s 150 -o 30 -m '{"author": "John Doe"}'
```

### Detailed Steps

1. **Read Text from Standard Input**:
   The script reads the text to be split from standard input.

2. **Split Text into Chunks**:
   The text is split into chunks using the `RecursiveCharacterTextSplitter`. The chunk size and overlap can be customized using command-line arguments.

3. **Add Metadata**:
   Metadata can be added to each chunk. The metadata is provided as a JSON string through the `-m` or `--metadata` argument.

4. **Output Chunks in JSON Format**:
   The processed chunks are output in JSON format.

## Example Output

```json
[
  {
    "page_content": "This is the first chunk of text.",
    "metadata": {
      "author": "John Doe"
    }
  },
  {
    "page_content": "This is the second chunk of text with some overlap.",
    "metadata": {
      "author": "John Doe"
    }
  }
]
```