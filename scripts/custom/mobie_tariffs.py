import logging
import os
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests

# URL of the page containing the download link
PAGE_URL = "https://www.mobie.pt/pt/redemobie/encontrar-posto"
DIR_OUTPUT = "data/naps/portugal/history_tariffs/"
DIR_LATEST = "data/naps/portugal/mobie_tariffs_latest.csv"
os.makedirs(DIR_OUTPUT, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
)

# Download the HTML page
response = session.get(PAGE_URL, timeout=20)
response.raise_for_status()
html = response.text

# Use BeautifulSoup to find the download link
soup = BeautifulSoup(html, "html.parser")
download_link_tag = soup.find("a", id="linkDownload")
if not download_link_tag or not download_link_tag.has_attr("href"):
    raise Exception("Download link not found in HTML.")
download_url = download_link_tag["href"]

# If the link is relative, build the absolute URL
if not download_url.startswith("http"):
    download_url = urljoin(PAGE_URL, download_url)

# Download the CSV file
csv_response = session.get(download_url, timeout=30)
csv_response.raise_for_status()

# Save the file with date in the filename
date_str = datetime.now().strftime("%Y%m%d")
filename = f"mobie_{date_str}.csv"
filepath = os.path.join(DIR_OUTPUT, filename)
with open(filepath, "wb") as f:
    f.write(csv_response.content)
logging.info(f"Downloaded CSV to {filepath}")
# Update the latest tariffs file
with open(DIR_LATEST, "wb") as f:
    f.write(csv_response.content)
logging.info(f"Updated latest tariffs file at {DIR_LATEST}")
