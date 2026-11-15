
import requests
import csv
import json
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://quotes.toscrape.com/"
OUTPUT_CSV = "output.csv"
OUTPUT_JSON = "output.json"

session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

quotes_data = []
url = BASE_URL

while url:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        quotes = soup.select(".quote")

        for item in quotes:
            quote_text = item.select_one(".text").get_text(strip=True)
            author = item.select_one(".author").get_text(strip=True)

            tags = [
                tag.get_text(strip=True)
                for tag in item.select(".tags a.tag")
            ]

            quotes_data.append({
                "quote": quote_text,
                "author": author,
                "tags": tags
            })

        print(f"Scraped {len(quotes)} quotes from {url}")

        next_page = soup.select_one("li.next a")

        if next_page:
            url = BASE_URL.rstrip("/") + next_page["href"]
            time.sleep(2)
        else:
            url = None

    except requests.RequestException as error:
        print(f"Request failed: {error}")
        break

    except Exception as error:
        print(f"Unexpected error: {error}")
        break

# Save data to CSV
try:
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["quote", "author", "tags"]
        )
        writer.writeheader()

        for item in quotes_data:
            writer.writerow({
                "quote": item["quote"],
                "author": item["author"],
                "tags": ", ".join(item["tags"])
            })

    # Save data to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(quotes_data, file, indent=4, ensure_ascii=False)

    # Summary report
    print("\n--- Scraping Summary ---")
    print(f"Total quotes: {len(quotes_data)}")
    print(f"Unique authors: {len(set(item['author'] for item in quotes_data))}")
    print(f"CSV saved: {OUTPUT_CSV}")
    print(f"JSON saved: {OUTPUT_JSON}")

except OSError as error:
    print(f"File saving failed: {error}")

finally:
    session.close()
