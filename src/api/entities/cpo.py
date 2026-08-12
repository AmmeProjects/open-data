from dataclasses import dataclass


@dataclass
class CPO:
    id: str
    id_ext: str
    # ID Derived from External EVSE-ID (different from national operator ID)
    name: str
    country_code: str
    website: str
    vat_id: str
    telephone: str
    display_name: str = None
    parent_id: str = None
    # For future use if we want to link CPOs to a parent organization
