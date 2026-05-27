import json

from src.mappers.naps.portugal import extract_cpos, parse_nap_data
from src.utils.download import Download
from src.utils.serialize import default_serializer
from src.utils.xml import xml_to_json

URL = "https://pgm.mobie.pt/integration/nap/evChargingInfra"
PATH = "data/raw/portugal_mobie_static.xml"
OUTPUT_PATH = "data/naps/portugal/locations.json"
CPO_OUTPUT_PATH = "data/naps/portugal/cpos.json"
FORCE_DOWNLOAD = False


def update_locations():

    # Download XML from Portuguese NAP:
    Download(url=URL, path=PATH).download(force=FORCE_DOWNLOAD)

    # Convert to JSON:
    path_json = xml_to_json(PATH)

    # Convert to OCPI format:
    container = parse_nap_data(path_json=path_json)

    # Extract and store CPO register:
    cpos = extract_cpos(
        path_json=path_json, mapping_path="data/naps/portugal/cpo_enrichement_data.yml"
    )

    # Store locations:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        str_out = json.dumps(
            container, default=default_serializer, indent=2, ensure_ascii=False
        )
        fp.write(str_out + "\n")  # Ensure newline at end of file

    # Store CPO register:
    with open(CPO_OUTPUT_PATH, "w", encoding="utf-8") as fp:
        str_out = json.dumps(
            cpos, default=default_serializer, indent=2, ensure_ascii=False
        )
        fp.write(str_out + "\n")  # Ensure newline at end of file


if __name__ == "__main__":
    update_locations()
