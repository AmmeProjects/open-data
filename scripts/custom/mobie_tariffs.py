import re
import requests
import os
from datetime import datetime
import logging
from bs4 import BeautifulSoup  # Added for robust HTML parsing

# URL of the page containing the download link
PAGE_URL = "https://www.mobie.pt/pt/redemobie/encontrar-posto"
DIR_OUTPUT = "data/naps/portugal/history_tariffs/"
DIR_LATEST = "data/naps/portugal/mobie_tariffs_latest.csv"
os.makedirs(DIR_OUTPUT, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Download the HTML page
response = requests.get(PAGE_URL, timeout=20)
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
    from urllib.parse import urljoin
    download_url = urljoin(PAGE_URL, download_url)

# Download the CSV file
csv_response = requests.get(download_url)
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
