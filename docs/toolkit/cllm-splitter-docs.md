# CLLM Splitter Docs CLI Tool

## Overview
The `cllm-splitter-docs` CLI tool is designed to split text documents into smaller chunks using the `RecursiveCharacterTextSplitter`. This can be useful for processing large texts in manageable pieces, with optional overlap between chunks.

## Usage

### Command Line Arguments

- `-s`, `--chunk_size`
  - **Type:** `int`
  - **Default:** `1000`
  - **Description:** Specifies the maximum size of each chunk in characters. This determines how large each split text segment will be.

- `-o`, `--chunk_overlap`
  - **Type:** `int`
  - **Default:** `10`
  - **Description:** Specifies the number of characters that overlap between consecutive chunks. This can help maintain context between chunks.

### Example

To split a document with a chunk size of 500 characters and an overlap of 50 characters, you would use the following command:

```sh
cllm-splitter-docs -s 500 -o 50
```

This will read the input documents from standard input, split them according to the specified chunk size and overlap, and print the resulting chunks in JSON format.

## Input and Output

- **Input:** The tool expects a JSON array of documents from standard input. Each document should be a dictionary with at least a `"page_content"` key containing the text to be split.
- **Output:** The tool outputs a JSON array of documents to standard output, where each document contains a chunk of the original text and its associated metadata.

## Example Input

```json
[
  {
    "page_content": "This is a long text document that needs to be split into smaller chunks.",
    "metadata": {"title": "Example Document"}
  }
]
```

## Example Output

```json
[
  {
    "page_content": "This is a long text document that needs to be split into smaller",
    "metadata": {"title": "Example Document"}
  },
  {
    "page_content": "chunks.",
    "metadata": {"title": "Example Document"}
  }
]
```

By using the `cllm-splitter-docs` CLI tool, you can efficiently manage and process large text documents by breaking them down into smaller, more manageable pieces.
