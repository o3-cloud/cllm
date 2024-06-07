# cllm-load-website CLI Tool

`cllm-load-website` is a command-line tool designed to scrape webpages and output their content in either text or HTML format. Below are the details on how to use the CLI arguments for this tool.

## CLI Arguments

### `-o`, `--output`
- **Description**: Specify the output type.
- **Usage**: Define the format of the output content. Acceptable values are `text` or `html`.
- **Default**: `text`
- **Example**: 
  ```sh
  cllm-load-website -o html
  ```

### `-b`, `--browser`
- **Description**: Specify the browser type.
- **Usage**: Choose the browser to be used for scraping. Acceptable values are `chrome` or `firefox`.
- **Default**: `chrome`
- **Example**: 
  ```sh
  cllm-load-website -b firefox
  ```

### `-u`, `--url`
- **Description**: URL to scrape.
- **Usage**: Provide a single URL to scrape. If not provided, the tool will read URLs from standard input.
- **Example**: 
  ```sh
  cllm-load-website -u https://example.com
  ```

## Example Usage

### Scraping a Single URL in Text Format Using Chrome
```sh
cllm-load-website -u https://example.com
```

### Scraping a Single URL in HTML Format Using Firefox
```sh
cllm-load-website -o html -b firefox -u https://example.com
```

### Reading URLs from Standard Input
```sh
echo '["https://example1.com", "https://example2.com"]' | cllm-load-website
```

By using these arguments, you can customize the behavior of the `cllm-load-website` tool to fit your specific scraping needs.
