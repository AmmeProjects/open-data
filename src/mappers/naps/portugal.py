import json
from datetime import datetime
from datetime import timezone
from src.api.ocpi import Location
from src.api.ocpi import EVSE
from src.api.ocpi import Connector
from src.api.ocpi import GeoLocation
from src.api.ocpi import ParkingType
from src.api.ocpi import Capabilities
from src.api.ocpi import ConnectorStandards
from src.api.ocpi import ConnectorFormats
from src.api.ocpi import PowerTypes
from src.api.container import DataContainer
from src.conversion.datex2 import DatexCapabilities
from src.conversion.datex2 import DatexConnectorFormats
from src.conversion.datex2 import DatexPowerTypes
from src.conversion.datex2 import DatexConnectorStandards



def parse_connector(doc) -> Connector:
    datex_standard = DatexConnectorStandards(doc['ns6:connectorType'])
    datex_format = DatexConnectorFormats(doc['ns6:connectorFormat'])
    power_type = DatexPowerTypes(doc['ns6:chargingMode'])
    return Connector(
        id="",
        standard=ConnectorStandards[datex_standard.name],
        format=ConnectorFormats[datex_format.name],
        power_type=PowerTypes[power_type.name],
        max_voltage=int(float(doc['ns6:voltage'])) if 'ns6:voltage' in doc else None,
        max_amperage=int(float(doc['ns6:maximumCurrent'])) if 'ns6:maximumCurrent' in doc else None,
        max_electric_power=int(float(doc['ns6:maxPowerAtSocket'])) if 'ns6:maxPowerAtSocket' in doc else None,
        last_updated="",
    )


def parse_evse(doc) -> EVSE:
    connectors = doc['ns6:connector']
    if not isinstance(connectors, list):
        connectors = [connectors]
    
    return EVSE(
        uid=doc['@id'],
        evse_id=doc['ns4:externalIdentifier'] if 'ns4:externalIdentifier' in doc else doc['@id'],
        status="UNKNOWN",
        capabilities=[],
        connectors=[parse_connector(conn) for conn in connectors],
        last_updated="",
    )


def parse_location(doc) -> Location:
    operator_id = doc['ns4:operator']['@id']
    party_id = operator_id

    address = doc['ns4:locationReference']['ns3:_locationReferenceExtension']['ns3:facilityLocation']['ns2:address']['ns2:addressLine']['ns2:text']['values']['value']['#text']
    city = doc['ns4:locationReference']['ns3:_locationReferenceExtension']['ns3:facilityLocation']['ns2:address']['ns2:city']['values']['value']['#text']
    state = None  # Not present in example
    postal_code = doc['ns4:locationReference']['ns3:_locationReferenceExtension']['ns3:facilityLocation']['ns2:address']['ns2:postcode']
    country_code = doc['ns4:locationReference']['ns3:_locationReferenceExtension']['ns3:facilityLocation']['ns2:address']['ns2:countryCode']

    coordinates = doc['ns4:locationReference']['ns3:pointByCoordinates']['ns3:pointCoordinates']
    latitude = float(coordinates['ns3:latitude'])
    longitude = float(coordinates['ns3:longitude'])

    evses = doc['ns6:energyInfrastructureStation']['ns6:refillPoint']
    if not isinstance(evses, list):
        evses = [evses]

    last_updated = datetime.fromisoformat(doc['ns4:lastUpdated'].replace('Z', '+00:00')).astimezone(timezone.utc).replace(tzinfo=None).isoformat()
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
        operator=doc['ns4:operator']['ns4:name']['values']['value']['#text'],
        opening_times=None,
        last_updated=last_updated,
    )

    capabilities = doc['ns6:energyInfrastructureStation'].get('ns6:authenticationAndIdentificationMethods', [])
    if isinstance(capabilities, str):
        capabilities = [capabilities]
    
    for evse in location.evses:
        evse.capabilities = [
            Capabilities[DatexCapabilities(c).name]
            for c in capabilities
        ]
        evse.last_updated = location.last_updated
        for i, connector in enumerate(evse.connectors):
            connector.id = "*".join([evse.evse_id, str(i)])
            connector.last_updated = evse.last_updated
    
    return location


def parse_nap_data(path_json) -> DataContainer:
    # Extract payload:
    data_dict = json.load(open(path_json))
    field_payload = list(data_dict.keys())[0]
    data_dict = data_dict[field_payload]

    
    # Extract stations from infrastructure table:
    egilocations = data_dict["ns6:energyInfrastructureTable"]['ns6:energyInfrastructureSite']
    print("Locations found:", len(egilocations))

    # Transform to OCPI locations:
    locations = [parse_location(loc) for loc in egilocations]

    # Put data into container
    container = DataContainer(
        data=locations, 
        timestamp=datetime.now(tz=timezone.utc).isoformat()
    )

    return container
