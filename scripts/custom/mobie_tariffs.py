import json
import logging
import os
import shutil
from datetime import datetime

from amme_open_data.utils.download import Download

TARIFFS_URL = "https://data.mobie.pt/data/tariffs.json"
DIR_OUTPUT = "data/naps/portugal/history_tariffs/"
PATH_LATEST = "data/naps/portugal/mobie_tariffs_latest.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


def update_tariffs() -> None:
    os.makedirs(DIR_OUTPUT, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(DIR_OUTPUT, f"mobie_{date_str}.json")

    Download(url=TARIFFS_URL, path=filepath).download(force=True)

    # Validate and pretty-print JSON payload
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    logging.info("Downloaded and formatted JSON to %s", filepath)

    shutil.copyfile(filepath, PATH_LATEST)
    logging.info("Updated latest tariffs file at %s", PATH_LATEST)


if __name__ == "__main__":
    update_tariffs()
