from dataclasses import dataclass
from .enums import ParkingType
from .enums import ConnectorFormats
from .enums import ConnectorStandards
from .enums import PowerTypes
from .enums import Capabilities


@dataclass
class GeoLocation:
    latitude: float
    longitude: float


@dataclass
class Connector:
    id: str
    standard: ConnectorStandards
    format: ConnectorFormats
    power_type: PowerTypes
    max_voltage: int | None
    max_amperage: int | None
    max_electric_power: int | None
    last_updated: str


@dataclass
class EVSE:
    uid: str
    evse_id: str
    status: str
    # status_schedule: str
    capabilities: list[Capabilities]
    connectors: list[Connector]
    # floor_level: str
    # coordinates: str
    # physical_reference: str
    # directions: str
    # parking_restrictions: str
    # images: str
    last_updated: str


@dataclass
class Location:
    country_code: str
    party_id: str
    id: str
    publish: bool
    name: str
    address: str
    city: str
    postal_code: str
    state: str
    country: str
    coordinates: GeoLocation
    # related_locations: str
    parking_type: ParkingType

    evses: list[EVSE]
    
    operator: str
    opening_times: str
    # authentication_methods: str

    last_updated: str
    