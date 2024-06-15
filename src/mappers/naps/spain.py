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
from src.conversion.datex2 import DatexCapabilities
from src.conversion.datex2 import DatexConnectorFormats
from src.conversion.datex2 import DatexPowerTypes
from src.conversion.datex2 import DatexConnectorStandards
from src.conversion.datex2 import DatexParkingType


def _enum_values(en):
    return {v for v in en}

def _enum_names(en):
    return {v.name for v in en}


def parse_connector(doc) -> Connector:
    datex_standard = DatexConnectorStandards(doc['egi:connectorType'])
    datex_format = DatexConnectorFormats(doc['egi:connectorFormat'])
    power_type = DatexPowerTypes(doc['egi:chargingMode'])
    return Connector(
        id="",
        standard= ConnectorStandards[datex_standard.name],
        format=ConnectorFormats[datex_format.name],
        power_type=PowerTypes[power_type.name],
        max_voltage=int(float(doc['egi:voltage'])) if 'egi:voltage' in doc else None,
        max_amperage=int(float(doc['egi:maximumCurrent'])) if 'egi:maximumCurrent' in doc else None,
        max_electric_power=int(float(doc['egi:maxPowerAtSocket'])) if 'egi:maxPowerAtSocket' in doc else None,
        last_updated="",
    )


def parse_evse(doc) -> EVSE:
    connectors = doc['egi:connector']
    if not isinstance(connectors, list):
        connectors = [connectors]
    
    return EVSE(
        uid=doc['@id'],
        evse_id=doc['fac:name']['com:values']['com:value']['#text'],
        status="UNKNOWN",
        # status_schedule=None,
        capabilities=[],
        connectors=[parse_connector(conn) for conn in connectors],
        last_updated="",
    )


def parse_site(doc) -> Location:

    operator_id = doc['fac:operator']['@id']
    party_id = operator_id.split("*")[1] if "*" in operator_id else operator_id

    address = doc['fac:locationReference']['loc:_locationReferenceExtension']['loc:facilityLocation']['locx:address']['locx:addressLine'][0]['locx:text']['com:values']['com:value']['#text']
    city = doc['fac:locationReference']['loc:_locationReferenceExtension']['loc:facilityLocation']['locx:address']['locx:addressLine'][1]['locx:text']['com:values']['com:value']['#text']
    state = doc['fac:locationReference']['loc:_locationReferenceExtension']['loc:facilityLocation']['locx:address']['locx:addressLine'][2]['locx:text']['com:values']['com:value']['#text']

    evses = doc['egi:energyInfrastructureStation']['egi:refillPoint']
    if not isinstance(evses, list):
        evses = [evses]

    datex_parking_type = DatexParkingType(doc.get('egi:typeOfSite')) if 'egi:typeOfSite' in doc and doc.get('egi:typeOfSite') in _enum_values(DatexParkingType) else None

    last_updated = datetime.fromisoformat(doc['fac:lastUpdated']).astimezone(timezone.utc).replace(tzinfo=None).isoformat()
    location = Location(
        country_code="es",
        party_id=party_id,
        id=doc["@id"],
        publish=True,
        name=doc['fac:name']['com:values']['com:value']['#text'],
        address=":".join(address.split(":")[1:]).strip(),
        city=":".join(city.split(":")[1:]).strip(),
        postal_code=doc['fac:locationReference']['loc:_locationReferenceExtension']['loc:facilityLocation']['locx:address']['locx:postcode'],
        state=":".join(state.split(":")[1:]).strip(),
        country="ESP",
        coordinates=GeoLocation(
            latitude=float(doc['fac:locationReference']['loc:coordinatesForDisplay']['loc:latitude']),
            longitude=float(doc['fac:locationReference']['loc:coordinatesForDisplay']['loc:longitude']),
        ),
        parking_type=ParkingType[datex_parking_type.name] if datex_parking_type is not None else None,
        evses=[parse_evse(pt) for pt in evses],
        
        operator=doc['fac:operator']['fac:name']['com:values']['com:value']['#text'],
        opening_times=doc['fac:operatingHours']['fac:label'],
        last_updated=last_updated,
    )

    # update capabilities and update timestamp on evses
    capabilities = doc['egi:energyInfrastructureStation'].get('egi:authenticationAndIdentificationMethods', [])
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
