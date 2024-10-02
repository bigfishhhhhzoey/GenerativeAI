import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import os
import pandas as pd

# Regex pattern to match a URL
HTTP_URL_PATTERN = r'^http[s]*://.+'

class HyperlinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hyperlinks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.hyperlinks.append(attrs["href"])

# Function to get the hyperlinks from a URL
def get_hyperlinks(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if not response.info().get('Content-Type').startswith("text/html"):
                return []
            html = response.read().decode('utf-8')
    except Exception as e:
        print(e)
        return []
    
    parser = HyperlinkParser()
    parser.feed(html)
    return parser.hyperlinks

# Function to get the hyperlinks from a URL that are within the same domain
def get_domain_hyperlinks(local_domain, url):
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None
        if re.search(HTTP_URL_PATTERN, link):
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link
        else:
            if link.startswith("/"):
                clean_link = f"https://{local_domain}/{link[1:]}"
        if clean_link and clean_link.endswith("/"):
            clean_link = clean_link[:-1]
        if clean_link:
            clean_links.append(clean_link)
    return list(set(clean_links))

def remove_newlines(text):
    return text.replace('\n', ' ').replace('\\n', ' ').replace('  ', ' ')

# Function to crawl the website and save the scraped data to a CSV file
def crawl_website(full_url, limit):
    local_domain = urlparse(full_url).netloc
    queue = deque([full_url])
    seen = set([full_url])

    if not os.path.exists(f"text/{local_domain}/"):
        os.makedirs(f"text/{local_domain}/")
    if not os.path.exists("processed"):
        os.makedirs("processed")

    url_count = 0
    texts = []

    while queue and url_count < limit:
        url = queue.pop()
        print(f"Crawling: {url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
            text = soup.get_text()
            if "You need to enable JavaScript to run this app." in text:
                print(f"Skipping {url} due to JavaScript requirement.")
                continue

            # Save the text to a file
            filename = f'text/{local_domain}/{url[8:].replace("/", "_")}.txt'
            with open(filename, "w") as f:
                f.write(text)
            
            texts.append((filename, remove_newlines(text)))
            url_count += 1
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        for link in get_domain_hyperlinks(local_domain, url):
            if link not in seen and url_count < limit:
                queue.append(link)
                seen.add(link)

    # After crawling, write all the scraped data into a CSV file
    if texts:
        df = pd.DataFrame(texts, columns=['filename', 'text'])
        df.to_csv('processed/scraped.csv', index=False)
        print(f"Scraped data saved to 'processed/scraped.csv'.")
    else:
        print("No data scraped.")

    print(f"Finished crawling. Total URLs crawled: {url_count}")

if __name__ == "__main__":
    full_url = input("Enter the website URL to crawl: ").strip()
    limit = int(input("Enter the maximum number of URLs to crawl: "))
    crawl_website(full_url, limit)
