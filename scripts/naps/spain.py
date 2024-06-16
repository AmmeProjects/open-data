import json
from src.utils.download import Download
from src.utils.xml import xml_to_json
from src.utils.serialize import default_serializer
from src.mappers.naps.spain import parse_nap_data


URL             = "https://infocar.dgt.es/datex2/v3/miterd/EnergyInfrastructureTablePublication/electrolineras.xml"
PATH            = "data/raw/electrolineras.xml"
OUTPUT_PATH     = "data/naps/spain/locations.json"
FORCE_DOWNLOAD  = False


def update_locations():

    # Download XML from spanish NAP:
    Download(url=URL, path=PATH).download(force=FORCE_DOWNLOAD)

    # Convert to JSON:
    path_json = xml_to_json(PATH)
    
    # Convert to OPCI format:
    container = parse_nap_data(path_json=path_json)

    # Serialize and store:
    with open(OUTPUT_PATH, "w") as fp:
        json.dump(container, fp, default=default_serializer, indent=2, ensure_ascii=False)


if __name__ == "__main__":

    update_locations()
