import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import json

def generate_sitemap(start_url, browser):
    if browser == 'chrome':
        driver = webdriver.Chrome()
    else:
        driver = webdriver.Firefox()
    driver.get(start_url)
    domain = urlparse(start_url).netloc
    domain = "https://" + domain

    urls = set()
    elements = driver.find_elements(By.TAG_NAME, 'a')
    for element in elements:
        url = element.get_attribute('href')
        if url and url.startswith(domain):
            urls.add(url)

    driver.quit()
    return list(urls)

def main():
    parser = argparse.ArgumentParser(description='Generate a sitemap from a given URL.')
    parser.add_argument('-u', '--url', type=str, help='The URL to generate the sitemap from.')
    parser.add_argument('-b', '--browser', type=str, help='The browser to use for generating the sitemap. Options are "chrome" and "firefox". Default is "firefox".', default='firefox')
    args = parser.parse_args()

    sitemap = generate_sitemap(args.url, args.browser)
    print(json.dumps(sitemap, indent=2))


if __name__ == '__main__':
    main()