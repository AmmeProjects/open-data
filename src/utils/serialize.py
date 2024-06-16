import json
from enum import Enum


def default_serializer(o):
    if isinstance(o, Enum):
        return o.name
    return o.__dict__
