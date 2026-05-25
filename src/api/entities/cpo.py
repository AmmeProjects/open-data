from dataclasses import dataclass


@dataclass
class CPO:
    id: str
    name: str
    country_code: str
    website: str
    vat_id: str
    telephone: str
    id_parent: str = None  # For future use if we want to link CPOs to a parent organization
