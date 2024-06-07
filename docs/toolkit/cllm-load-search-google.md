# cllm-load-search-google CLI Tool

`cllm-load-search-google` is a command-line tool designed to scrape Google search results based on specified queries and parameters. Below is the documentation for the CLI arguments usage.

## CLI Arguments

### Positional Arguments

- `query` (optional): 
  - **Type**: `str`
  - **Description**: The search query to be used for scraping Google search results. If not provided, the tool will read queries from standard input (stdin).
  - **Default**: `""` (empty string)

### Optional Arguments

- `-t`, `--time_range`:
  - **Type**: `TimeRange`
  - **Choices**: `d` (day), `w` (week), `m` (month), `y` (year)
  - **Description**: Specifies the time range for the search results.
  - **Default**: `w` (week)

- `-b`, `--browser`:
  - **Type**: `str`
  - **Choices**: `chrome`, `firefox`
  - **Description**: Specifies the browser to use for scraping.
  - **Default**: `firefox`

- `-e`, `--exclude_list`:
  - **Type**: `str`
  - **nargs**: `+` (one or more values)
  - **Description**: A list of domains to exclude from the search results.
  - **Default**: `['google.com', 'youtube.com']`

- `-l`, `--limit`:
  - **Type**: `int`
  - **Description**: The limit for the number of search results to return.
  - **Default**: `20`

### Example Usage

```sh
# Basic usage with a query
cllm-load-search-google "example query"

# Specifying a time range of one month
cllm-load-search-google "example query" -t m

# Using Chrome browser for scraping
cllm-load-search-google "example query" -b chrome

# Excluding specific domains from the results
cllm-load-search-google "example query" -e example.com anotherexample.com

# Limiting the number of results to 10
cllm-load-search-google "example query" -l 10
```

### Reading Queries from Standard Input

If no query is provided as a positional argument, the tool will read queries from standard input (stdin). This can be useful for batch processing multiple queries.

```sh
# Reading queries from a JSON file
cat queries.json | cllm-load-search-google
```

In this example, `queries.json` should contain a JSON array of queries.

```
[
    "query1",
    "query2",
    "query3"
]
```