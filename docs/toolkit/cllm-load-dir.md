# cllm-load-dir CLI Tool Documentation

`cllm-load-dir` is a command-line tool designed to load files from a specified directory, split them into chunks, and optionally save the processed data as a JSON file.

## Usage

```sh
cllm-load-dir -d <directory> [options]
```

## Arguments

### Required Arguments

- `-d, --directory`
  - **Type:** `str`
  - **Description:** The directory to load files from.
  - **Example:** `-d /path/to/directory`

### Optional Arguments

- `-g, --glob_pattern`
  - **Type:** `str`
  - **Default:** `"**/*"`
  - **Description:** The glob pattern to match files within the directory.
  - **Example:** `-g "*.txt"`

- `-s, --chunk_size`
  - **Type:** `int`
  - **Default:** `1000`
  - **Description:** The size of each chunk in characters.
  - **Example:** `-s 500`

- `-o, --chunk_overlap`
  - **Type:** `int`
  - **Default:** `10`
  - **Description:** The number of characters that overlap between chunks.
  - **Example:** `-o 20`

- `-m, --use_multithreading`
  - **Action:** `store_true`
  - **Description:** Use multithreading for loading files. This flag does not require a value.
  - **Example:** `-m`

- `-f, --output_file`
  - **Type:** `str`
  - **Description:** The output file path for the JSON data. If not provided, the JSON data will be printed to the console.
  - **Example:** `-f output.json`

## Example Command

```sh
cllm-load-dir -d /path/to/directory -g "*.txt" -s 500 -o 20 -m -f output.json
```

This command will load all `.txt` files from `/path/to/directory`, split them into chunks of 500 characters with an overlap of 20 characters, use multithreading for loading, and save the resulting JSON data to `output.json`.
