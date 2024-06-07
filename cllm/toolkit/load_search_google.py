import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from urllib.parse import quote_plus
from enum import Enum
import argparse

class TimeRange(Enum):
    DAY = 'd'
    WEEK = 'w'
    MONTH = 'm'
    YEAR = 'y'


def setup_driver(browser):
    if browser.lower() == 'firefox':
        service = FirefoxService(GeckoDriverManager().install())
        options = webdriver.FirefoxOptions()
        return webdriver.Firefox(service=service, options=options)
    else:
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        return webdriver.Chrome(service=service, options=options)


def scrape_google_search(queries, time_range, exclude_list, limit=20, browser='chrome'):
    driver = setup_driver(browser)
    base_url = 'https://www.google.com/search?q='
    results = []

    for query in queries:
        encoded_query = quote_plus(query)
        search_url = f"{base_url}{encoded_query}&tbs=qdr:{time_range.value}"
        driver.get(search_url)
        time.sleep(2)

        search_results = driver.find_elements(By.CSS_SELECTOR, 'a')
        results.extend(result.get_attribute('href') for result in search_results)
    
    driver.quit()

    filtered_urls = [url for url in results if url and not any(exclude in url for exclude in exclude_list)]
    return filtered_urls[:limit]


def main():

    parser = argparse.ArgumentParser(description="Scrape Google search results")
    parser.add_argument('query', type=str, help='Search query', default="", nargs='?')
    parser.add_argument('-t', '--time_range', type=TimeRange, choices=list(TimeRange), help='Time range for search results', default=TimeRange.WEEK)
    parser.add_argument('-b', '--browser', type=str, choices=['chrome', 'firefox'], help='Browser to use for scraping', default='firefox')
    parser.add_argument('-e', '--exclude_list', type=str, nargs='+', default=['google.com', 'youtube.com'], help='List of domains to exclude from the results')
    parser.add_argument('-l', '--limit', type=int, help='Limit for number of results', default=20)
    args = parser.parse_args()

    queries = []

    if args.query:
        queries = [args.query]
    else:
        std_in = sys.stdin.read()
        queries = json.loads(std_in)

    urls = scrape_google_search(queries, args.time_range, args.exclude_list, args.limit, args.browser)
    print(json.dumps(urls, indent=2))


if __name__ == "__main__":
    main()
