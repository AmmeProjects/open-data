import json
from datetime import datetime, timezone

import yaml

from src.api.container import DataContainer
from src.api.entities.cpo import CPO
from src.api.ocpi import (
    EVSE,
    Capabilities,
    Connector,
    ConnectorFormats,
    ConnectorStandards,
    GeoLocation,
    Location,
    PowerTypes,
)
from src.conversion.datex2 import (
    DatexCapabilities,
    DatexConnectorFormats,
    DatexConnectorStandards,
    DatexPowerTypes,
)
from src.utils.strings import remove_spaces


def parse_connector(doc) -> Connector:
    datex_standard = DatexConnectorStandards(doc["ns6:connectorType"])
    datex_format = DatexConnectorFormats(doc["ns6:connectorFormat"])
    power_type = DatexPowerTypes(doc["ns6:chargingMode"])
    return Connector(
        id="",
        standard=ConnectorStandards[datex_standard.name],
        format=ConnectorFormats[datex_format.name],
        power_type=PowerTypes[power_type.name],
        max_voltage=int(float(doc["ns6:voltage"])) if "ns6:voltage" in doc else None,
        max_amperage=int(float(doc["ns6:maximumCurrent"]))
        if "ns6:maximumCurrent" in doc
        else None,
        max_electric_power=int(float(doc["ns6:maxPowerAtSocket"]))
        if "ns6:maxPowerAtSocket" in doc
        else None,
        last_updated="",
    )


def parse_evse(doc) -> EVSE:
    connectors = doc["ns6:connector"]
    if not isinstance(connectors, list):
        connectors = [connectors]

    return EVSE(
        uid=doc["@id"],
        evse_id=doc["ns4:externalIdentifier"]
        if "ns4:externalIdentifier" in doc
        else doc["@id"],
        status="UNKNOWN",
        capabilities=[],
        connectors=[parse_connector(conn) for conn in connectors],
        last_updated="",
    )


def parse_location(doc) -> Location:
    operator_id = doc["ns4:operator"]["@id"]
    party_id = operator_id

    address = doc["ns4:locationReference"]["ns3:_locationReferenceExtension"][
        "ns3:facilityLocation"
    ]["ns2:address"]["ns2:addressLine"]["ns2:text"]["values"]["value"]["#text"]
    city = doc["ns4:locationReference"]["ns3:_locationReferenceExtension"][
        "ns3:facilityLocation"
    ]["ns2:address"]["ns2:city"]["values"]["value"]["#text"]
    state = None  # Not present in example
    postal_code = doc["ns4:locationReference"]["ns3:_locationReferenceExtension"][
        "ns3:facilityLocation"
    ]["ns2:address"]["ns2:postcode"]
    country_code = doc["ns4:locationReference"]["ns3:_locationReferenceExtension"][
        "ns3:facilityLocation"
    ]["ns2:address"]["ns2:countryCode"]

    coordinates = doc["ns4:locationReference"]["ns3:pointByCoordinates"][
        "ns3:pointCoordinates"
    ]
    latitude = float(coordinates["ns3:latitude"])
    longitude = float(coordinates["ns3:longitude"])

    evses = doc["ns6:energyInfrastructureStation"]["ns6:refillPoint"]
    if not isinstance(evses, list):
        evses = [evses]

    last_updated = (
        datetime.fromisoformat(doc["ns4:lastUpdated"].replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
        .isoformat()
    )
    location = Location(
        country_code=country_code,
        party_id=party_id,
        id=doc["@id"],
        publish=True,
        name=doc["@id"],
        address=address,
        city=city,
        postal_code=postal_code,
        state=state,
        country=country_code,
        coordinates=GeoLocation(
            latitude=latitude,
            longitude=longitude,
        ),
        parking_type=None,
        evses=[parse_evse(pt) for pt in evses],
        operator=doc["ns4:operator"]["ns4:name"]["values"]["value"]["#text"],
        opening_times=None,
        last_updated=last_updated,
    )

    capabilities = doc["ns6:energyInfrastructureStation"].get(
        "ns6:authenticationAndIdentificationMethods", []
    )
    if isinstance(capabilities, str):
        capabilities = [capabilities]

    for evse in location.evses:
        evse.capabilities = [
            Capabilities[DatexCapabilities(c).name] for c in capabilities
        ]
        evse.last_updated = location.last_updated
        for i, connector in enumerate(evse.connectors):
            connector.id = "*".join([evse.evse_id, str(i)])
            connector.last_updated = evse.last_updated

    return location


def parse_nap_data(path_json) -> DataContainer:

    # Extract payload:
    with open(path_json, "r", encoding="utf-8") as json_fp:
        data_dict = json.load(json_fp)
    field_payload = list(data_dict.keys())[0]
    data_dict = data_dict[field_payload]

    # Extract stations from infrastructure table:
    egilocations = data_dict["ns6:energyInfrastructureTable"][
        "ns6:energyInfrastructureSite"
    ]
    print("Locations found:", len(egilocations))

    # Transform to OCPI locations:
    locations = [parse_location(loc) for loc in egilocations]

    # Put data into container
    container = DataContainer(
        data=locations, timestamp=datetime.now(tz=timezone.utc).isoformat()
    )

    return container


def extract_cpos(path_json, mapping_path=None) -> list[CPO]:
    """
    Extracts a unique list of CPOs and their metadata from the Portuguese NAP JSON.
    Allows passing a mapping_path to a JSON file to manually enrich CPO data.
    """
    # Extract payload:
    with open(path_json, "r", encoding="utf-8") as json_fp:
        data_dict = json.load(json_fp)

    # Load CPO mapping if provided
    cpo_mapping = {}
    if mapping_path:
        with open(mapping_path, "r", encoding="utf-8") as map_fp:
            data = yaml.safe_load(map_fp)
            cpo_mapping = {item["id"]: item for item in data.get("cpos", [])}

    field_payload = list(data_dict.keys())[0]
    data_dict = data_dict[field_payload]

    egilocations = data_dict.get("ns6:energyInfrastructureTable", {}).get(
        "ns6:energyInfrastructureSite", []
    )

    cpos = {}
    for doc in egilocations:
        operator_doc = doc.get("ns4:operator")
        if not operator_doc:
            continue

        operator_id = operator_doc.get("@id")
        if not operator_id:
            continue

        # Determine the name: check mapping first
        mapped_cpo = cpo_mapping.get(operator_id, {})

        name = (
            operator_doc.get("ns4:name", {})
            .get("values", {})
            .get("value", {})
            .get("#text")
        )

        # If CPO already exists, check if we can update the name (some stations have more detailed operator names than others)
        if operator_id in cpos and len(name) > len(cpos[operator_id].name):
            cpos[operator_id].name = name
            continue

        country_code = (
            doc.get("ns4:locationReference", {})
            .get("ns3:_locationReferenceExtension", {})
            .get("ns3:facilityLocation", {})
            .get("ns2:address", {})
            .get("ns2:countryCode")
        )

        website = operator_doc.get("ns4:linkToGeneralInformation")
        vat_id = operator_doc.get("ns4:vatIdentificationNumber")

        telephone = None
        org_unit = operator_doc.get("ns4:organisationUnit")
        if org_unit:
            contact = org_unit.get("ns4:contactInformation")
            if contact:
                telephone = contact.get("ns4:telephoneNumber")

        # --- ENRICHMENT ---
        # Get display name
        display_name = mapped_cpo.get("display_name")
        parent_id = mapped_cpo.get("parent_id")

        # --- END OF ENRICHMENT ---

        cpos[operator_id] = CPO(
            id=operator_id,
            name=name,
            display_name=display_name,
            country_code=country_code,
            website=website,
            vat_id=remove_spaces(vat_id),
            telephone=remove_spaces(telephone),
            parent_id=parent_id,
        )

    # Order CPOs by ID and return as list
    cpos = dict(sorted(cpos.items(), key=lambda item: item[0]))

    return list(cpos.values())
