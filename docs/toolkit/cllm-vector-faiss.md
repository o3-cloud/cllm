# FAISS Index Tool

This CLI tool allows you to create, save, and read FAISS indexes using OpenAI embeddings. It supports two main operations: saving documents to a FAISS index and performing similarity searches on an existing FAISS index.

## Usage

The CLI tool supports two main operations: `save` and `read`.

### Save Operation

The `save` operation allows you to save documents to a FAISS index. The documents should be provided in JSON format via standard input.

#### Example

```bash
echo '[{"page_content": "This is a test document.", "metadata": {"id": 1}}]' | cllm-vector-faiss -i my_index -m text-embedding-3-small save
```

### Read Operation

The `read` operation allows you to perform a similarity search on an existing FAISS index.

#### Example

```bash
cllm-vector-faiss -i my_index -m text-embedding-3-small read "test document" -k 5
```

## Configuration

The tool uses environment variables for configuration. You can set these variables in your environment or in a `.env` file.

- `CLLM_DIR`: Directory where the FAISS indexes will be stored. Default is `$(pwd)/.cllm`.
- `CLLM_LOGLEVEL`: Logging level. Default is `INFO`.

## Logging

The tool uses Python's built-in logging module. You can configure the logging level using the `CLLM_LOGLEVEL` environment variable.

## Command Line Arguments

- `-i, --index`: Name of the FAISS index (required).
- `-m, --model`: Name of the OpenAI embedding model to use (default: `text-embedding-3-small`).
- `-k, --results`: Number of documents to return (default: 5).
- `operation`: Operation to perform on the FAISS index (`read` or `save`).
- `query`: Query string to search for (required for `read` operation).
