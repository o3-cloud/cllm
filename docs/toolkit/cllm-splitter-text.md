# cllm-splitter-text CLI Tool Documentation

## Overview
`cllm-splitter-text` is a command-line tool designed to split text into chunks using the `RecursiveCharacterTextSplitter`. This tool is useful for processing large texts by breaking them down into smaller, manageable pieces with optional overlapping characters and associated metadata.

## Usage
```sh
cllm-splitter-text [OPTIONS]
```

## Options

### `-s, --chunk_size`
- **Description**: Specifies the maximum size of each chunk.
- **Type**: `int`
- **Default**: `100`
- **Example**: 
  ```sh
  cllm-splitter-text -s 150
  ```

### `-o, --chunk_overlap`
- **Description**: Specifies the number of characters that overlap between chunks.
- **Type**: `int`
- **Default**: `20`
- **Example**: 
  ```sh
  cllm-splitter-text -o 30
  ```

### `-m, --metadata`
- **Description**: Provides metadata to be associated with each chunk. The metadata should be in JSON format.
- **Type**: `json.loads`
- **Default**: `'{}'`
- **Example**: 
  ```sh
  cllm-splitter-text -m '{"author": "John Doe", "date": "2023-10-01"}'
  ```

## Example Command
```sh
echo "Your large text here" | cllm-splitter-text -s 150 -o 30 -m '{"author": "John Doe"}'
```

This command reads the text from standard input, splits it into chunks of up to 150 characters with 30 characters overlapping between chunks, and associates the metadata `{"author": "John Doe"}` with each chunk. The resulting chunks are then printed in JSON format.
