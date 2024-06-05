import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from urllib.parse import urlparse, urljoin
import json
import time
import logging
import requests
from requests.exceptions import RequestException

logging.basicConfig(level=os.environ.get("CLLM_LOGLEVEL"))

def create_driver(browser, headless):
    if browser == 'chrome':
        options = ChromeOptions()
        if headless:
            options.add_argument('--headless')
        return webdriver.Chrome(options=options)
    else:
        options = FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        return webdriver.Firefox(options=options)

def is_valid_url(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except RequestException:
        return False

def generate_sitemap(start_url, browser, delay, headless):
    driver = create_driver(browser, headless)
    domain = urlparse(start_url).netloc
    domain = "https://" + domain
    visited_urls = set()
    sitemap = []


    visited_urls.add(start_url)
    try:
        driver.get(start_url)
        time.sleep(delay)
    except Exception as e:
        logging.error(f"Error accessing {start_url}: {e}")
        return

    elements = driver.find_elements(By.TAG_NAME, 'a')
    for element in elements:
        href = element.get_attribute('href')
        if href and href.startswith(domain):
            full_url = urljoin(domain, href)
            if full_url not in visited_urls:
                sitemap.append(full_url)

    driver.quit()
    return sitemap

def main():
    parser = argparse.ArgumentParser(description='Generate a sitemap from a given URL.')
    parser.add_argument('-u', '--url', type=str, required=True, help='The URL to generate the sitemap from.')
    parser.add_argument('-b', '--browser', type=str, choices=['chrome', 'firefox'], default='firefox', help='The browser to use for generating the sitemap. Options are "chrome" and "firefox". Default is "firefox".')
    parser.add_argument('-l', '--delay', type=int, default=1, help='Delay between requests in seconds. Default is 1.')
    parser.add_argument('-H', '--headless', action='store_true', help='Run browser in headless mode. Default is False.')
    args = parser.parse_args()

    if not is_valid_url(args.url):
        logging.error("Invalid URL or network issue.")
        return

    sitemap = generate_sitemap(args.url, args.browser, args.delay, args.headless)
    print(json.dumps(sitemap, indent=2))

if __name__ == '__main__':
    main()
