# cllm-load-google-search: A Command-Line Tool for Scraping Google Search Results

## Overview

`cllm-load-google-search` is a command-line tool designed to scrape Google search results based on specified queries, time ranges, and other customizable options. The tool supports both Chrome and Firefox browsers for scraping and allows users to exclude specific domains from the results.

## Features

- Scrape Google search results for multiple queries.
- Filter results based on a specified time range.
- Exclude specific domains from the search results.
- Limit the number of results returned.
- Support for both Chrome and Firefox browsers.

## Usage

To use `cllm-load-google-search`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- `query`: **(Optional)** The search query. If not provided, queries will be read from standard input.
- `-t`, `--time_range`: The time range for search results. Choices are `DAY`, `WEEK`, `MONTH`, `YEAR`. Default is `WEEK`.
- `-b`, `--browser`: The browser to use for scraping. Choices are `chrome`, `firefox`. Default is `firefox`.
- `-e`, `--exclude_list`: List of domains to exclude from the results. Default is `['google.com', 'youtube.com']`.
- `-l`, `--limit`: Limit for the number of results. Default is `20`.

### Example Command

```bash
echo '["example query"]' | cllm-load-google-search -t WEEK -b chrome -e google.com youtube.com -l 10
```

### Detailed Steps

1. **Set Up the Driver**:
   The script sets up the web driver for either Chrome or Firefox based on the specified browser argument.

2. **Construct Search URL**:
   For each query, the script constructs a Google search URL with the specified time range.

3. **Open the URL**:
   The script opens the constructed URL using the web driver and waits for the page to load.

4. **Scrape URLs**:
   The script scrapes the URLs from the search results and filters out any URLs that match the domains in the exclude list.

5. **Return Results**:
   The script returns the filtered URLs, limited to the specified number of results.

## Example Output

```json
[
  "https://example.com/page1",
  "https://example.com/page2",
  "https://example.com/page3"
]
```