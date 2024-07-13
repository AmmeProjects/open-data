"""
Functions to extract data from supercharge.info and transform it.

Examples:
1. Run extract and transform:
    `python -m scripts.cpos.tesla_supercharge`
2. Run transform:
    `python -m scripts.cpos.tesla_supercharge --skip-extract`
"""

import argparse
import requests
import json
import pandas as pd


URL = (
    "https://supercharge.info/service/supercharge/sites"
    "?draw=1"
    "&columns%5B0%5D%5Bdata%5D=&columns%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=name&columns%5B1%5D%5Bname%5D=&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=address.street&columns%5B2%5D%5Bname%5D=&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=address.city&columns%5B3%5D%5Bname%5D=&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=address.state&columns%5B4%5D%5Bname%5D=&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=address.zip&columns%5B5%5D%5Bname%5D=&columns%5B5%5D%5Bsearchable%5D=true&columns%5B5%5D%5Borderable%5D=true&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=address.country&columns%5B6%5D%5Bname%5D=&columns%5B6%5D%5Bsearchable%5D=true&columns%5B6%5D%5Borderable%5D=true&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata%5D=function&columns%5B7%5D%5Bname%5D=&columns%5B7%5D%5Bsearchable%5D=true&columns%5B7%5D%5Borderable%5D=true&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bdata%5D=elevationMeters&columns%5B8%5D%5Bname%5D=&columns%5B8%5D%5Bsearchable%5D=true&columns%5B8%5D%5Borderable%5D=true&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bdata%5D=stallCount&columns%5B9%5D%5Bname%5D=&columns%5B9%5D%5Bsearchable%5D=true&columns%5B9%5D%5Borderable%5D=true&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bdata%5D=powerKilowatt&columns%5B10%5D%5Bname%5D=&columns%5B10%5D%5Bsearchable%5D=true&columns%5B10%5D%5Borderable%5D=true&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B11%5D%5Bdata%5D=function&columns%5B11%5D%5Bname%5D=&columns%5B11%5D%5Bsearchable%5D=true&columns%5B11%5D%5Borderable%5D=true&columns%5B11%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B11%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B12%5D%5Bdata%5D=dateOpened&columns%5B12%5D%5Bname%5D=&columns%5B12%5D%5Bsearchable%5D=true&columns%5B12%5D%5Borderable%5D=true&columns%5B12%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B12%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=11&order%5B0%5D%5Bdir%5D=desc&order%5B1%5D%5Bcolumn%5D=1&order%5B1%5D%5Bdir%5D=asc"
    "&start={start}"
    "&length={length}"
    "&search="
    "&regionId=101&" # EU
    "countryId="
    "&state="
    "&status=OPEN"
    "&stalls="
    "&power="
    "&stallType="
    "&plugType="
    "&parking="
    "&openTo="
    "&solarCanopy="
    "&battery="
)


def get_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Check if the response is JSON
        if response.headers.get('Content-Type', '').startswith('application/json'):
            return response.json()
        else:
            return response.text
    
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def download_pages():
    
    print("Downloading supercharger locations...")
    page_length = 100

    # Get total number of records
    total_records = get_data(URL.format(start=0, length=0)).get("recordCount")
    
    # Iterate pages
    records = []
    for i in range(0, total_records + 1, page_length):
        records.extend(
            get_data(URL.format(start=i, length=page_length)).get("results")
        )

    # Save data
    with open("data/opcs/europe_tesla.json", "w") as f:
        json.dump(records, f)

    print("Success!")


def process_count_locations_all_users():
    
    with open("data/opcs/europe_tesla.json", "r") as f:
        records = json.load(f)
    
    df = (
        pd.json_normalize(records)
        .loc[lambda _: _["address.country"] != "Morocco"]
        .groupby(["address.country", "otherEVs"])
        .size()
        .unstack(-1, fill_value=0)
        .assign(percent_all_evs=lambda _: _[True].div(_.sum(axis=1)).mul(100).round(1))
        
        .rename(
            index={
                "Czech Republic": "Czech Rep.",
            },
            columns={
                False: "tesla_only",
                True: "all_evs",
            }
        )
        .reset_index()
    )
    df.to_csv("data/processed/tesla/europe_tesla_all_evs.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description="Script to load and process data from supercharge.info")
    parser.add_argument("--skip-extract", action="store_true", help="Skip extract")
    parser.add_argument("--skip-transform", action="store_true", help="Skip transform")
    
    args = parser.parse_args()

    if not (args.skip_extract or args.skip_transform):
        parser.error("At least one step must be specified")

    if not args.skip_extract:
        download_pages()
    
    if not args.skip_transform:
        process_count_locations_all_users()


if __name__ == "__main__":
    main()
