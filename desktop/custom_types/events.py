from dataclasses import dataclass, field
from enum import Enum

@dataclass
class Event:
    class EventType(Enum):
        NAVIGATE = "navigate"
        
    type: EventType
    properties: dict[str, str] = field(default_factory=dict)