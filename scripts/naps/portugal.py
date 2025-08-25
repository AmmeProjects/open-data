import json
from src.utils.download import Download
from src.utils.xml import xml_to_json
from src.utils.serialize import default_serializer
from src.mappers.naps.portugal import parse_nap_data


URL             = "https://pgm.mobie.pt/integration/nap/evChargingInfra"
PATH            = "data/raw/portugal_mobie_static.xml"
OUTPUT_PATH     = "data/naps/portugal/locations.json"
FORCE_DOWNLOAD  = False


def update_locations():

    # Download XML from Portuguese NAP:
    Download(url=URL, path=PATH).download(force=FORCE_DOWNLOAD)

    # Convert to JSON:
    path_json = xml_to_json(PATH)
    
    # Convert to OCPI format:
    container = parse_nap_data(path_json=path_json)

    # Serialize and store:
    with open(OUTPUT_PATH, "w") as fp:
        json.dump(container, fp, default=default_serializer, indent=2, ensure_ascii=False)


if __name__ == "__main__":

    update_locations()
