# cllm-load-webpages: A Command-Line Tool for Webpage Scraping

## Overview

`cllm-load-webpages` is a command-line tool designed to scrape content from a list of URLs. The tool supports both Chrome and Firefox browsers and offers options to output the scraped content as either text or HTML. Additionally, it includes a debugging mode to facilitate troubleshooting.

## Features

- Scrape content from a list of URLs.
- Support for Chrome and Firefox browsers.
- Option to output scraped content as text or HTML.
- Debugging mode to assist with troubleshooting.

## Usage

To use `cllm-load-webpages`, you need to run the script with the appropriate arguments. Below is the detailed usage information.

### Command-Line Arguments

- `-d`, `--debug`: Enable debugging mode.
- `-o`, `--output`: Output type (text or html). Default is `text`.
- `-b`, `--browser`: Browser type (chrome or firefox). Default is `chrome`.

### Example Command

```bash
echo '["http://example.com", "http://example.org"]' | cllm-load-webpages -o html -b firefox
```

### Detailed Steps

1. **Initialize the WebDriver**:
   The script initializes the WebDriver based on the specified browser type (Chrome or Firefox). If debugging mode is enabled, it sets up the WebDriver to connect to a running instance of the browser.

2. **Scrape Webpages**:
   For each URL in the input list, the script navigates to the webpage, waits for it to load, and then scrapes the content. The content can be extracted as plain text or HTML based on the specified output type.

3. **Output the Results**:
   The scraped content is stored in a list of dictionaries, each containing the page content and metadata (URL). The results are then converted to JSON format and printed to the console.

## Example Output

```json
[
  {
    "page_content": "<html>...</html>",
    "metadata": {
      "url": "http://example.com"
    }
  },
  {
    "page_content": "<html>...</html>",
    "metadata": {
      "url": "http://example.org"
    }
  }
]
```