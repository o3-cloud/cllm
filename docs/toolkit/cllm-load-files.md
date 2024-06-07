# cllm-load-files CLI Tool Documentation

## Usage

The `cllm-load-files` CLI tool is designed to load and split files into chunks. Below are the details of the command-line arguments you can use with this tool.

### Positional Arguments

- `files` (str, optional): A JSON string representing the list of files to load. If not provided, the tool will read from standard input (stdin).

### Optional Arguments

- `-s`, `--chunk_size` (int, default=1000): Specifies the size of each chunk in characters. The default value is 1000 characters.
  
- `-o`, `--chunk_overlap` (int, default=10): Specifies the number of characters that overlap between consecutive chunks. The default value is 10 characters.

### Example Usage

```sh
# Using positional argument for files
cllm-load-files '["file1.txt", "file2.txt"]' -s 500 -o 20

# Using stdin for files
echo '["file1.txt", "file2.txt"]' | cllm-load-files -s 500 -o 20
```

This tool will output a JSON array of documents, where each document contains the `page_content` and `metadata` of the chunks created from the input files.
