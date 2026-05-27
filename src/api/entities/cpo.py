from dataclasses import dataclass


@dataclass
class CPO:
    id: str
    name: str
    country_code: str
    website: str
    vat_id: str
    telephone: str
    display_name: str = None
    parent_id: str = (
        None  # For future use if we want to link CPOs to a parent organization
    )
