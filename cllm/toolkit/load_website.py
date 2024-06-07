import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import json
import argparse

def scrape_webpages(search_urls, debug_mode, output_type, browser_type):
    # Initialize the driver
    if browser_type == 'firefox':
        options = FirefoxOptions()
        driver = webdriver.Firefox(options=options)
    else:
        options = Options()
        driver = webdriver.Chrome(options=options)

    if debug_mode:
        print("Debugging mode enabled")
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    results = []
    # For each search query
    for url in search_urls:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        scrape_results = driver.find_element(By.TAG_NAME, "body")
        if output_type == 'text':
            content = scrape_results.text
        else:
            content = scrape_results.get_attribute('outerHTML')
        results.append({"page_content": content, "metadata": {"url": url}})

    if debug_mode is False:
        driver.close()

    return json.dumps(results)

def main():
    parser = argparse.ArgumentParser(description="Scrape webpages")
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debugging mode')
    parser.add_argument('-o', '--output', help='Output type (text or html)', default='text')
    parser.add_argument('-b', '--browser', help='Browser type (chrome or firefox)', default='chrome')
    args = parser.parse_args()

    try:
        import sys
        input_data = sys.stdin.read()
        search_urls = json.loads(input_data)
        print(scrape_webpages(search_urls, args.debug, args.output, args.browser))
    except Exception as e:
        search_urls = []
        search_urls.append(input_data)
        print(scrape_webpages(search_urls, args.debug, args.output, args.browser))

if __name__ == "__main__":
    main()

