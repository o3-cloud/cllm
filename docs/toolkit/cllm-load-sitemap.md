# Sitemap Generator Script

This script generates a sitemap from a given URL using Selenium WebDriver. It supports both Chrome and Firefox browsers and can run in headless mode. The script also includes error handling for invalid URLs and network issues.

## Features

- **Browser Support**: Choose between Chrome and Firefox.
- **Headless Mode**: Option to run the browser in headless mode.
- **Delay Between Requests**: Configurable delay between requests to avoid overloading the server.
- **Error Handling**: Checks for valid URLs and handles network issues gracefully.

## Requirements

- Python 3.x
- Selenium
- Requests
- ChromeDriver or GeckoDriver (for Firefox)

## Usage

### Command Line Arguments

- `-u`, `--url`: The URL to generate the sitemap from. (Required)
- `-b`, `--browser`: The browser to use for generating the sitemap. Options are "chrome" and "firefox". Default is "firefox".
- `-l`, `--delay`: Delay between requests in seconds. Default is 1.
- `-H`, `--headless`: Run browser in headless mode. Default is False.

### Example

```sh
cllm-load-sitemap -u https://example.com -b chrome -l 2 -H
```

## Logging

The script uses Python's built-in logging module to log errors and other information. The log level can be set using the `CLLM_LOGLEVEL` environment variable.

## Notes

- Ensure that the appropriate WebDriver (ChromeDriver for Chrome, GeckoDriver for Firefox) is installed and available in your system's PATH.
- The script currently only follows links within the same domain as the start URL.
